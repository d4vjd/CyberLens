# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

import json
from uuid import uuid4

from fastapi import HTTPException
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cyberlens.common.time_utils import utc_now
from cyberlens.detection.evaluators import (
    AggregationEvaluator,
    BaseEvaluator,
    PatternEvaluator,
    SequenceEvaluator,
    ThresholdEvaluator,
)
from cyberlens.detection.models import Alert, DetectionRule, MitreTechniqueCoverage, RuleType
from cyberlens.detection.rule_loader import RuleLoader
from cyberlens.detection.schemas import (
    AlertDetail,
    AlertListResponse,
    RuleHistoricalTestResponse,
    RuleMutationResponse,
    RuleSummary,
)
from cyberlens.ingestion.models import Event
from cyberlens.ingestion.models import SeverityLevel
from cyberlens.streaming.publisher import publish_alert


class DetectionService:
    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self.session = session
        self.redis = redis
        self.evaluators: dict[RuleType, BaseEvaluator] = {
            RuleType.THRESHOLD: ThresholdEvaluator(),
            RuleType.PATTERN: PatternEvaluator(),
            RuleType.SEQUENCE: SequenceEvaluator(),
            RuleType.AGGREGATION: AggregationEvaluator(),
        }

    async def list_rules(self) -> list[RuleSummary]:
        rules = await self._get_enabled_rules()
        stats_rows = (
            await self.session.execute(
                select(
                    Alert.rule_id,
                    func.count(Alert.id),
                    func.max(Alert.created_at),
                ).group_by(Alert.rule_id)
            )
        ).all()
        stats = {
            rule_id: {
                "historical_matches": int(match_count or 0),
                "last_triggered_at": last_triggered_at,
            }
            for rule_id, match_count, last_triggered_at in stats_rows
        }
        return [
            RuleSummary.model_validate(rule).model_copy(update=stats.get(rule.id, {}))
            for rule in rules
        ]

    async def list_alerts(self, offset: int, limit: int) -> AlertListResponse:
        stmt = select(Alert).order_by(Alert.created_at.desc()).offset(offset).limit(limit)
        items = [AlertDetail.model_validate(item) for item in (await self.session.scalars(stmt)).all()]
        total = int((await self.session.scalar(select(func.count()).select_from(Alert))) or 0)
        return AlertListResponse(items=items, total=total, offset=offset, limit=limit)

    async def get_alert(self, alert_id: int) -> AlertDetail:
        alert = await self.session.get(Alert, alert_id)
        if alert is None:
            raise HTTPException(status_code=404, detail="Alert not found")
        return AlertDetail.model_validate(alert)

    async def save_rule_yaml(self, yaml_content: str) -> RuleMutationResponse:
        loader = RuleLoader()
        payload = loader.parse_rule_yaml(yaml_content)
        existing = await self.session.scalar(
            select(DetectionRule).where(DetectionRule.rule_id == payload["id"])
        )
        file_path = loader.save_rule_file(payload, existing=existing)
        await loader.sync_to_database(self.session)
        rule = await self.session.scalar(
            select(DetectionRule).where(DetectionRule.rule_id == payload["id"])
        )
        assert rule is not None
        return RuleMutationResponse(
            rule_id=rule.rule_id,
            title=rule.title,
            file_path=str(file_path),
            enabled=rule.enabled,
            message="Rule YAML saved and detection catalog reloaded.",
        )

    async def retire_rule(self, rule_id: str) -> RuleMutationResponse:
        loader = RuleLoader()
        rule = await self.session.scalar(select(DetectionRule).where(DetectionRule.rule_id == rule_id))
        if rule is None:
            raise HTTPException(status_code=404, detail="Rule not found")

        file_path = loader.delete_rule_file(rule)
        rule.enabled = False
        rule_definition = dict(rule.rule_definition or {})
        rule_definition["enabled"] = False
        rule.rule_definition = rule_definition
        await self.session.commit()

        return RuleMutationResponse(
            rule_id=rule.rule_id,
            title=rule.title,
            file_path=str(file_path),
            enabled=rule.enabled,
            message="Rule retired from the active catalog and its YAML file was removed.",
        )

    async def test_rule_yaml(self, yaml_content: str, limit: int) -> RuleHistoricalTestResponse:
        loader = RuleLoader()
        payload = loader.parse_rule_yaml(yaml_content)
        temp_rule_id = f"{payload['id']}-test-{uuid4().hex[:8]}"
        rule = DetectionRule(
            rule_id=temp_rule_id,
            title=payload["title"],
            description=payload.get("description"),
            severity=SeverityLevel(payload["severity"]),
            rule_type=RuleType(payload["type"]),
            rule_definition=payload,
            mitre_tactic=(payload.get("mitre") or {}).get("tactic"),
            mitre_technique_id=(payload.get("mitre") or {}).get("technique_id"),
            enabled=True,
        )

        recent_events = (
            await self.session.scalars(
                select(Event).order_by(Event.timestamp.desc(), Event.id.desc()).limit(limit)
            )
        ).all()
        ordered_events = list(reversed(recent_events))
        evaluator = self.evaluators[rule.rule_type]
        generated_alerts = 0
        sample_event_ids: list[int] = []
        sample_matches: list[dict[str, object]] = []

        try:
            for event in ordered_events:
                evaluation = await evaluator.evaluate(self.redis, self._event_payload(event), rule)
                if not evaluation.matched:
                    continue
                generated_alerts += 1
                for matched in evaluation.matched_events:
                    event_id = matched.get("id")
                    if isinstance(event_id, int) and event_id not in sample_event_ids and len(sample_event_ids) < 10:
                        sample_event_ids.append(event_id)
                    if len(sample_matches) < 5:
                        sample_matches.append(matched)
        finally:
            await self._clear_rule_runtime_state(rule.rule_id)

        return RuleHistoricalTestResponse(
            rule_id=payload["id"],
            title=payload["title"],
            evaluated_events=len(ordered_events),
            generated_alerts=generated_alerts,
            sample_event_ids=sample_event_ids,
            sample_matches=sample_matches,
        )

    async def process_stream_event(self, stream_event: dict[str, str]) -> list[Alert]:
        event_id = int(stream_event["id"])
        event = await self.session.get(Event, event_id)
        if event is None:
            return []

        event_payload = self._event_payload(event)
        generated: list[Alert] = []
        for rule in await self._get_enabled_rules():
            evaluator = self.evaluators[rule.rule_type]
            evaluation = await evaluator.evaluate(self.redis, event_payload, rule)
            if not evaluation.matched:
                continue
            alert = Alert(
                alert_uid=str(uuid4()),
                rule_id=rule.id,
                title=rule.title,
                severity=rule.severity,
                source_ip=event.source_ip,
                mitre_tactic=rule.mitre_tactic,
                mitre_technique_id=rule.mitre_technique_id,
                matched_events=evaluation.matched_events,
            )
            self.session.add(alert)
            await self.session.flush()
            await self._update_coverage(rule, alert)
            generated.append(alert)

        if generated:
            await self.session.commit()
            for alert in generated:
                await publish_alert(self.redis, alert)
        else:
            await self.session.rollback()
        return generated

    async def _update_coverage(self, rule: DetectionRule, alert: Alert) -> None:
        if not rule.mitre_technique_id or not rule.mitre_tactic:
            return

        existing = await self.session.scalar(
            select(MitreTechniqueCoverage).where(
                MitreTechniqueCoverage.rule_id == rule.id,
                MitreTechniqueCoverage.technique_id == rule.mitre_technique_id,
            )
        )
        if existing is None:
            existing = MitreTechniqueCoverage(
                technique_id=rule.mitre_technique_id,
                tactic=rule.mitre_tactic,
                rule_id=rule.id,
                alert_count=1,
                last_alert_at=utc_now(),
            )
            self.session.add(existing)
            return

        existing.alert_count += 1
        existing.last_alert_at = alert.created_at or utc_now()

    def _event_payload(self, event: Event) -> dict[str, str | int | dict[str, object] | None]:
        return {
            "id": event.id,
            "timestamp": event.timestamp.isoformat(),
            "source_ip": event.source_ip,
            "dest_ip": event.dest_ip,
            "source_port": event.source_port,
            "dest_port": event.dest_port,
            "protocol": event.protocol,
            "action": event.action,
            "severity": event.severity.value,
            "event_type": event.event_type,
            "source_system": event.source_system,
            "hostname": event.hostname,
            "username": event.username,
            "message": event.message,
            "raw_log": event.raw_log,
            "parsed_data": event.parsed_data,
        }

    async def _get_enabled_rules(self) -> list[DetectionRule]:
        return (
            await self.session.scalars(
                select(DetectionRule).where(DetectionRule.enabled.is_(True)).order_by(DetectionRule.title)
            )
        ).all()

    async def _clear_rule_runtime_state(self, rule_id: str) -> None:
        keys: list[str] = []
        async for key in self.redis.scan_iter(match=f"rule:{rule_id}:*"):
            keys.append(key if isinstance(key, str) else key.decode("utf-8"))
        async for key in self.redis.scan_iter(match=f"alert:dedup:{rule_id}:*"):
            keys.append(key if isinstance(key, str) else key.decode("utf-8"))
        if keys:
            await self.redis.delete(*keys)


def parse_stream_payload(payload: dict[str, str]) -> dict[str, object]:
    parsed: dict[str, object] = {}
    for key, value in payload.items():
        if key == "parsed_data":
            parsed[key] = json.loads(value)
        else:
            parsed[key] = value
    return parsed