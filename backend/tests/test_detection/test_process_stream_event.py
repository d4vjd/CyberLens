# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from cyberlens.detection.evaluators.base import DetectionEvaluation
from cyberlens.detection.models import DetectionRule, RuleType
from cyberlens.detection.service import DetectionService
from cyberlens.ingestion.models import Event, SeverityLevel


class FakeSession:
    def __init__(self, event: Event) -> None:
        self.event = event

    async def get(self, _: object, __: object) -> Event:
        return self.event

    def add(self, _: object) -> None:
        return None

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


class FakeRedis:
    pass


class AssertingEvaluator:
    async def evaluate(
        self, redis: FakeRedis, event: dict[str, object], rule: DetectionRule
    ) -> DetectionEvaluation:
        assert isinstance(redis, FakeRedis)
        assert isinstance(rule, DetectionRule)
        assert rule.rule_definition["detection"]["filter"]["event_type"] == "authentication"
        assert event["event_type"] == "authentication"
        return DetectionEvaluation(matched=False)


def test_process_stream_event_uses_detection_rule_models() -> None:
    event = Event(
        id=42,
        timestamp=datetime(2026, 3, 12, 12, 0, tzinfo=UTC),
        source_ip="198.51.100.24",
        dest_ip="10.0.0.10",
        source_port=44321,
        dest_port=22,
        protocol="tcp",
        action="failed",
        severity=SeverityLevel.HIGH,
        event_type="authentication",
        source_system="sshd",
        raw_log="failed ssh login",
        parsed_data={"username": "admin"},
        hostname="web-prod-01",
        username="admin",
        message="failed ssh login",
        is_demo=True,
    )
    session = FakeSession(event)
    service = DetectionService(session=session, redis=FakeRedis())
    service.evaluators = {RuleType.PATTERN: AssertingEvaluator()}

    async def run() -> None:
        service._get_enabled_rules = lambda: _return_rules()  # type: ignore[method-assign]
        alerts = await service.process_stream_event({"id": "42"})
        assert alerts == []

    async def _return_rules() -> list[DetectionRule]:
        return [
            DetectionRule(
                id=1,
                rule_id="test_rule",
                title="Test Rule",
                description="Regression test",
                severity=SeverityLevel.HIGH,
                rule_type=RuleType.PATTERN,
                rule_definition={
                    "id": "test_rule",
                    "title": "Test Rule",
                    "severity": "high",
                    "type": "pattern",
                    "detection": {"filter": {"event_type": "authentication"}},
                },
                mitre_tactic="credential-access",
                mitre_technique_id="T1110",
                enabled=True,
            )
        ]

    asyncio.run(run())
