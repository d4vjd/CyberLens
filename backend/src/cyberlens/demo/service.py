# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from redis.asyncio import Redis
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cyberlens.common.time_utils import utc_now
from cyberlens.config import get_settings
from cyberlens.demo.schemas import (
    DataClearResponse,
    DemoCounts,
    DemoSeedRequest,
    DemoSeedResponse,
    DemoStatusResponse,
)
from cyberlens.demo.seed import build_seed_dataset
from cyberlens.demo.types import DemoEventSpec
from cyberlens.detection.models import Alert, DetectionRule, MitreTechniqueCoverage
from cyberlens.detection.service import DetectionService
from cyberlens.incidents.models import (
    Case,
    CaseAlert,
    CaseEvent,
    CaseEvidence,
    CaseStatus,
    ResponseAction,
    ResponseActionType,
)
from cyberlens.incidents.schemas import (
    CaseCommentRequest,
    CaseFromAlertRequest,
    CaseUpdateRequest,
    PlaybookRunRequest,
    ResponseActionRequest,
)
from cyberlens.incidents.service import IncidentService
from cyberlens.ingestion.models import Event, SeverityLevel
from cyberlens.settings.service import SettingsService

DEMO_CASE_PREFIX = "DEMO:"
logger = logging.getLogger(__name__)


@dataclass(slots=True)
class GeneratedAlertSeed:
    id: int
    title: str


class DemoService:
    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self.session = session
        self.redis = redis

    async def get_status(self) -> DemoStatusResponse:
        settings_service = SettingsService(self.session)
        await settings_service.ensure_defaults()
        return DemoStatusResponse(
            demo=await settings_service.get_demo_settings(), counts=await self.get_counts()
        )

    async def get_counts(self) -> DemoCounts:
        event_count = int(
            (
                await self.session.scalar(
                    select(func.count()).select_from(Event).where(Event.is_demo.is_(True))
                )
            )
            or 0
        )
        case_count = int(
            (
                await self.session.scalar(
                    select(func.count())
                    .select_from(Case)
                    .where(Case.title.like(f"{DEMO_CASE_PREFIX}%"))
                )
            )
            or 0
        )
        alert_count = int(
            (
                await self.session.scalar(
                    select(func.count())
                    .select_from(Alert)
                    .where(Alert.assigned_to == "demo-seeded")
                )
            )
            or 0
        )
        return DemoCounts(events=event_count, alerts=alert_count, cases=case_count)

    async def seed_dataset(self, payload: DemoSeedRequest) -> DemoSeedResponse:
        settings_service = SettingsService(self.session)
        await settings_service.ensure_defaults()

        existing_counts = await self.get_counts()
        if (
            existing_counts.events > 0
            and existing_counts.alerts > 0
            and existing_counts.cases > 0
            and not payload.force
        ):
            seeded_at = utc_now()
            await settings_service.set_demo_runtime_state(seeded_at=seeded_at.isoformat())
            return DemoSeedResponse(
                seeded_events=0,
                generated_alerts=0,
                created_cases=0,
                seeded_at=seeded_at,
                skipped=True,
                message=(
                    "Demo dataset already exists."
                    " Seed was skipped to avoid duplicating showcase data."
                ),
            )

        settings = get_settings()
        specs = build_seed_dataset(
            days=payload.days,
            intensity=payload.intensity,
            event_count=payload.event_count or settings.demo_seed_event_count,
        )
        alerts = await self.ingest_specs(specs, tag_alerts_as_seeded=True)
        created_case_ids = await self._seed_cases(alerts)
        seeded_at = utc_now()
        await settings_service.set_demo_runtime_state(seeded_at=seeded_at.isoformat())
        return DemoSeedResponse(
            seeded_events=len(specs),
            generated_alerts=len(alerts),
            created_cases=len(created_case_ids),
            seeded_at=seeded_at,
            message="Demo dataset seeded into the live event store and detection pipeline.",
        )

    async def clear_seeded_demo_data(self) -> DataClearResponse:
        demo_case_ids = list(
            (
                await self.session.scalars(
                    select(Case.id).where(Case.title.like(f"{DEMO_CASE_PREFIX}%"))
                )
            ).all()
        )
        demo_alert_ids = list(
            (
                await self.session.scalars(
                    select(Alert.id).where(Alert.assigned_to == "demo-seeded")
                )
            ).all()
        )
        demo_event_count = int(
            (
                await self.session.scalar(
                    select(func.count()).select_from(Event).where(Event.is_demo.is_(True))
                )
            )
            or 0
        )

        await self._delete_related_data(case_ids=demo_case_ids, alert_ids=demo_alert_ids)
        if demo_event_count:
            await self.session.execute(delete(Event).where(Event.is_demo.is_(True)))
        await self._rebuild_mitre_coverage()
        await self.session.commit()

        settings_service = SettingsService(self.session)
        await settings_service.set_demo_runtime_state(
            seeded_at=None,
            enabled=False,
            generator_status="stopped",
        )

        return DataClearResponse(
            scope="seeded_demo",
            cleared_events=demo_event_count,
            cleared_alerts=len(demo_alert_ids),
            cleared_cases=len(demo_case_ids),
            message="Seeded demo events, demo alerts, and demo cases were removed.",
        )

    async def clear_live_data(self) -> DataClearResponse:
        case_ids = list((await self.session.scalars(select(Case.id))).all())
        alert_ids = list((await self.session.scalars(select(Alert.id))).all())
        event_count = int(
            (await self.session.scalar(select(func.count()).select_from(Event))) or 0
        )

        await self._delete_related_data(case_ids=case_ids, alert_ids=alert_ids)
        if event_count:
            await self.session.execute(delete(Event))
        await self._rebuild_mitre_coverage()
        await self.session.commit()

        settings_service = SettingsService(self.session)
        await settings_service.set_demo_runtime_state(
            seeded_at=None,
            enabled=False,
            generator_status="stopped",
        )

        return DataClearResponse(
            scope="live_data",
            cleared_events=event_count,
            cleared_alerts=len(alert_ids),
            cleared_cases=len(case_ids),
            message=(
                "All indexed events, alerts, cases, and linked investigation records were removed."
            ),
        )

    async def ingest_specs(
        self,
        specs: Sequence[DemoEventSpec],
        *,
        tag_alerts_as_seeded: bool = False,
    ) -> list[GeneratedAlertSeed]:
        events = [spec.to_event() for spec in specs]
        self.session.add_all(events)
        await self.session.flush()
        event_ids = [event.id for event in events]
        await self.session.commit()

        detection_service = DetectionService(session=self.session, redis=self.redis)
        alerts: list[GeneratedAlertSeed] = []
        for event_id in event_ids:
            generated = await detection_service.process_stream_event({"id": str(event_id)})
            alert_seeds = [
                GeneratedAlertSeed(id=alert.id, title=alert.title) for alert in generated
            ]
            if tag_alerts_as_seeded:
                for alert in generated:
                    alert.assigned_to = "demo-seeded"
                if generated:
                    await self.session.commit()
            alerts.extend(alert_seeds)
        return alerts

    async def _seed_cases(self, alerts: Sequence[GeneratedAlertSeed]) -> list[str]:
        existing_titles = set(
            (
                await self.session.scalars(
                    select(Case.title).where(Case.title.like(f"{DEMO_CASE_PREFIX}%"))
                )
            ).all()
        )

        alerts_by_title: dict[str, list[int]] = defaultdict(list)
        for alert in alerts:
            alerts_by_title[alert.title].append(alert.id)

        incident_service = IncidentService(self.session)
        created_case_uids: list[str] = []

        brute_force_title = f"{DEMO_CASE_PREFIX} SSH Brute Force Investigation"
        brute_force_ids = alerts_by_title.get("SSH Brute Force Attempt", [])
        if brute_force_ids and brute_force_title not in existing_titles:
            case = await incident_service.create_case_from_alert(
                brute_force_ids[0],
                CaseFromAlertRequest(
                    actor="demo-seed",
                    assigned_to="ahassan",
                    playbook_id="brute_force_response",
                    title=brute_force_title,
                ),
            )
            await incident_service.add_comment(
                case.case_uid,
                CaseCommentRequest(
                    actor="ahassan",
                    summary="Initial triage notes captured from the demo seed pipeline.",
                    details={"queue": "soc-primary"},
                ),
            )
            await incident_service.update_case(
                case.case_uid,
                CaseUpdateRequest(actor="ahassan", status=CaseStatus.IN_PROGRESS),
            )
            await self._safe_run_playbook(
                incident_service,
                case.case_uid,
                PlaybookRunRequest(actor="ahassan", playbook_id="brute_force_response"),
                fallback_actor="ahassan",
                fallback_summary=(
                    "Playbook asset unavailable during demo seed;" " manual workflow left in place."
                ),
            )
            created_case_uids.append(case.case_uid)

        lateral_title = f"{DEMO_CASE_PREFIX} Lateral Movement Escalation"
        lateral_ids = alerts_by_title.get("Lateral movement over SMB", [])
        if lateral_ids and lateral_title not in existing_titles:
            case = await incident_service.create_case_from_alert(
                lateral_ids[0],
                CaseFromAlertRequest(
                    actor="demo-seed",
                    assigned_to="mreyes",
                    playbook_id="lateral_movement_response",
                    title=lateral_title,
                ),
            )
            await incident_service.execute_response_action(
                case.case_uid,
                ResponseActionRequest(
                    actor="mreyes",
                    action_type=ResponseActionType.ISOLATE_HOST,
                    target="wks-finance-14",
                    alert_id=lateral_ids[0],
                    parameters={"reason": "demo-seeded containment"},
                ),
            )
            await incident_service.update_case(
                case.case_uid,
                CaseUpdateRequest(actor="mreyes", status=CaseStatus.ESCALATED),
            )
            created_case_uids.append(case.case_uid)

        exfiltration_title = f"{DEMO_CASE_PREFIX} Data Exfiltration Review"
        exfiltration_ids = alerts_by_title.get("Suspicious DNS exfiltration", [])
        if exfiltration_ids and exfiltration_title not in existing_titles:
            case = await incident_service.create_case_from_alert(
                exfiltration_ids[0],
                CaseFromAlertRequest(
                    actor="demo-seed",
                    assigned_to="mreyes",
                    playbook_id="data_exfiltration_response",
                    title=exfiltration_title,
                ),
            )
            await self._safe_run_playbook(
                incident_service,
                case.case_uid,
                PlaybookRunRequest(actor="mreyes", playbook_id="data_exfiltration_response"),
                fallback_actor="mreyes",
                fallback_summary=(
                    "Playbook asset unavailable during demo seed;"
                    " containment notes recorded manually."
                ),
            )
            await incident_service.add_comment(
                case.case_uid,
                CaseCommentRequest(
                    actor="mreyes",
                    summary="Containment completed during demo dataset creation.",
                    details={"resolution": "outbound channel blocked"},
                ),
            )
            await incident_service.update_case(
                case.case_uid,
                CaseUpdateRequest(
                    actor="mreyes",
                    status=CaseStatus.RESOLVED,
                    severity=SeverityLevel.CRITICAL,
                ),
            )
            created_case_uids.append(case.case_uid)

        return created_case_uids

    async def _safe_run_playbook(
        self,
        incident_service: IncidentService,
        case_uid: str,
        payload: PlaybookRunRequest,
        *,
        fallback_actor: str,
        fallback_summary: str,
    ) -> None:
        try:
            await incident_service.run_playbook(case_uid, payload)
        except FileNotFoundError:
            logger.warning("Playbook '%s' unavailable during demo seed", payload.playbook_id)
            await incident_service.add_comment(
                case_uid,
                CaseCommentRequest(
                    actor=fallback_actor,
                    summary=fallback_summary,
                    details={"playbook_id": payload.playbook_id, "fallback": True},
                ),
            )

    async def _delete_related_data(
        self,
        *,
        case_ids: Sequence[int],
        alert_ids: Sequence[int],
    ) -> None:
        evidence_paths: list[str] = []
        if case_ids:
            evidence_paths = list(
                (
                    await self.session.scalars(
                        select(CaseEvidence.file_path).where(CaseEvidence.case_id.in_(case_ids))
                    )
                ).all()
            )
            await self.session.execute(
                delete(ResponseAction).where(ResponseAction.case_id.in_(case_ids))
            )
            await self.session.execute(delete(CaseEvent).where(CaseEvent.case_id.in_(case_ids)))
            await self.session.execute(
                delete(CaseEvidence).where(CaseEvidence.case_id.in_(case_ids))
            )
            await self.session.execute(delete(CaseAlert).where(CaseAlert.case_id.in_(case_ids)))

        if alert_ids:
            await self.session.execute(
                delete(ResponseAction).where(ResponseAction.alert_id.in_(alert_ids))
            )
            await self.session.execute(delete(CaseAlert).where(CaseAlert.alert_id.in_(alert_ids)))
            await self.session.execute(delete(Alert).where(Alert.id.in_(alert_ids)))

        if case_ids:
            await self.session.execute(delete(Case).where(Case.id.in_(case_ids)))

        self._cleanup_evidence_files(evidence_paths)

    def _cleanup_evidence_files(self, file_paths: Sequence[str]) -> None:
        for raw_path in file_paths:
            try:
                path = Path(raw_path)
                if path.exists():
                    path.unlink()
            except OSError:
                logger.warning("Failed to delete evidence file during data clear: %s", raw_path)

    async def _rebuild_mitre_coverage(self) -> None:
        await self.session.execute(delete(MitreTechniqueCoverage))
        coverage_rows = (
            await self.session.execute(
                select(
                    DetectionRule.id,
                    DetectionRule.mitre_technique_id,
                    DetectionRule.mitre_tactic,
                    func.count(Alert.id),
                    func.max(Alert.created_at),
                )
                .join(Alert, Alert.rule_id == DetectionRule.id)
                .where(
                    DetectionRule.mitre_technique_id.is_not(None),
                    DetectionRule.mitre_tactic.is_not(None),
                )
                .group_by(
                    DetectionRule.id,
                    DetectionRule.mitre_technique_id,
                    DetectionRule.mitre_tactic,
                )
            )
        ).all()
        for rule_id, technique_id, tactic, alert_count, last_alert_at in coverage_rows:
            self.session.add(
                MitreTechniqueCoverage(
                    rule_id=rule_id,
                    technique_id=str(technique_id),
                    tactic=str(tactic),
                    alert_count=int(alert_count or 0),
                    last_alert_at=last_alert_at,
                )
            )
