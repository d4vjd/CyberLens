# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cyberlens.common.time_utils import utc_now
from cyberlens.config import get_settings
from cyberlens.detection.models import Alert, AlertStatus
from cyberlens.incidents.models import (
    Case,
    CaseAlert,
    CaseEvent,
    CaseEventType,
    CaseEvidence,
    CaseStatus,
    ResponseAction,
    ResponseActionStatus,
    ResponseActionType,
)
from cyberlens.incidents.playbook_runner import PlaybookRunner
from cyberlens.incidents.response_actions.block_ip import BlockIpAction
from cyberlens.incidents.response_actions.disable_account import DisableAccountAction
from cyberlens.incidents.response_actions.isolate_host import IsolateHostAction
from cyberlens.incidents.schemas import (
    CaseAlertSummary,
    CaseCommentRequest,
    CaseCreateRequest,
    CaseDetail,
    CaseEvidenceDetail,
    CaseEventDetail,
    CaseFromAlertRequest,
    CaseListResponse,
    CaseSummary,
    CaseUpdateRequest,
    EvidenceUploadResponse,
    PlaybookRunRequest,
    PlaybookRunResponse,
    ResponseActionDetail,
    ResponseActionRequest,
)
from cyberlens.ingestion.models import SeverityLevel

SLA_WINDOWS = {
    SeverityLevel.CRITICAL: (timedelta(minutes=15), timedelta(hours=4)),
    SeverityLevel.HIGH: (timedelta(hours=1), timedelta(hours=24)),
    SeverityLevel.MEDIUM: (timedelta(hours=4), timedelta(hours=72)),
    SeverityLevel.LOW: (timedelta(hours=24), timedelta(hours=168)),
}


class IncidentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.playbook_runner = PlaybookRunner()
        self.response_action_handlers = {
            ResponseActionType.BLOCK_IP: BlockIpAction(),
            ResponseActionType.ISOLATE_HOST: IsolateHostAction(),
            ResponseActionType.DISABLE_ACCOUNT: DisableAccountAction(),
        }

    async def list_cases(self) -> CaseListResponse:
        cases = (
            await self.session.scalars(select(Case).order_by(Case.created_at.desc()))
        ).all()

        items = []
        for case in cases:
            alert_count = int(
                (await self.session.scalar(select(func.count()).select_from(CaseAlert).where(CaseAlert.case_id == case.id)))
                or 0
            )
            evidence_count = int(
                (
                    await self.session.scalar(
                        select(func.count()).select_from(CaseEvidence).where(CaseEvidence.case_id == case.id)
                    )
                )
                or 0
            )
            items.append(
                CaseSummary(
                    id=case.id,
                    case_uid=case.case_uid,
                    title=case.title,
                    severity=case.severity,
                    status=case.status,
                    priority=case.priority,
                    assigned_to=case.assigned_to,
                    playbook_id=case.playbook_id,
                    sla_due_at=case.sla_due_at,
                    alert_count=alert_count,
                    evidence_count=evidence_count,
                    created_at=case.created_at,
                )
            )

        return CaseListResponse(items=items, total=len(items))

    async def get_case(self, case_uid: str) -> CaseDetail:
        case = await self._get_case(case_uid)
        return await self._build_case_detail(case)

    async def create_case(self, payload: CaseCreateRequest) -> CaseDetail:
        case = Case(
            case_uid=str(uuid4()),
            title=payload.title,
            description=payload.description,
            severity=payload.severity,
            priority=payload.priority,
            assigned_to=payload.assigned_to,
            playbook_id=payload.playbook_id,
            sla_due_at=self._compute_sla_due_at(payload.severity),
        )
        self.session.add(case)
        await self.session.flush()

        await self._add_timeline_event(
            case.id,
            event_type=CaseEventType.COMMENT,
            actor=payload.actor,
            summary="Case created",
            details={"title": payload.title},
        )

        for alert_id in payload.alert_ids:
            await self._link_alert(case, alert_id, payload.actor)

        await self.session.commit()
        return await self._build_case_detail(case)

    async def create_case_from_alert(self, alert_id: int, payload: CaseFromAlertRequest) -> CaseDetail:
        alert = await self.session.get(Alert, alert_id)
        if alert is None:
            raise HTTPException(status_code=404, detail="Alert not found")

        title = payload.title or f"Case for {alert.title}"
        case = Case(
            case_uid=str(uuid4()),
            title=title,
            description=f"Created from alert {alert.alert_uid}",
            severity=alert.severity,
            priority=self._priority_for_severity(alert.severity),
            assigned_to=payload.assigned_to,
            playbook_id=payload.playbook_id,
            sla_due_at=self._compute_sla_due_at(alert.severity),
        )
        self.session.add(case)
        await self.session.flush()
        await self._add_timeline_event(
            case.id,
            event_type=CaseEventType.COMMENT,
            actor=payload.actor,
            summary="Case created from alert",
            details={"alert_id": alert.id, "alert_uid": alert.alert_uid},
        )
        await self._link_alert(case, alert_id, payload.actor)
        await self.session.commit()
        return await self._build_case_detail(case)

    async def update_case(self, case_uid: str, payload: CaseUpdateRequest) -> CaseDetail:
        case = await self._get_case(case_uid)
        before_status = case.status

        for field in ("title", "description", "severity", "priority", "assigned_to", "playbook_id"):
            value = getattr(payload, field)
            if value is not None:
                setattr(case, field, value)

        if payload.severity is not None:
            case.sla_due_at = self._compute_sla_due_at(payload.severity)

        if payload.status is not None and payload.status != case.status:
            case.status = payload.status
            if payload.status in {CaseStatus.RESOLVED, CaseStatus.CLOSED}:
                case.resolved_at = utc_now()

        if payload.assigned_to is not None:
            await self._add_timeline_event(
                case.id,
                event_type=CaseEventType.ASSIGNMENT,
                actor=payload.actor,
                summary="Case assignment updated",
                details={"assigned_to": payload.assigned_to},
            )

        if payload.status is not None and payload.status != before_status:
            await self._add_timeline_event(
                case.id,
                event_type=CaseEventType.STATUS_CHANGE,
                actor=payload.actor,
                summary="Case status changed",
                details={"from": before_status.value, "to": payload.status.value},
            )

        await self.session.commit()
        return await self._build_case_detail(case)

    async def add_comment(self, case_uid: str, payload: CaseCommentRequest) -> CaseEventDetail:
        case = await self._get_case(case_uid)
        event = await self._add_timeline_event(
            case.id,
            event_type=CaseEventType.COMMENT,
            actor=payload.actor,
            summary=payload.summary,
            details=payload.details,
        )
        await self.session.commit()
        return CaseEventDetail.model_validate(event)

    async def upload_evidence(self, case_uid: str, actor: str, file: UploadFile) -> EvidenceUploadResponse:
        case = await self._get_case(case_uid)
        settings = get_settings()
        evidence_dir = settings.resolved_evidence_dir / case.case_uid
        evidence_dir.mkdir(parents=True, exist_ok=True)

        filename = file.filename or f"evidence-{uuid4().hex}.bin"
        destination = evidence_dir / filename
        content = await file.read()
        destination.write_bytes(content)

        evidence = CaseEvidence(
            case_id=case.id,
            filename=filename,
            file_path=str(destination),
            file_size=len(content),
            content_type=file.content_type or "application/octet-stream",
        )
        self.session.add(evidence)
        await self.session.flush()
        await self._add_timeline_event(
            case.id,
            event_type=CaseEventType.EVIDENCE_ADDED,
            actor=actor,
            summary="Evidence uploaded",
            details={"filename": filename, "file_size": len(content)},
        )
        await self.session.commit()
        return EvidenceUploadResponse(evidence=CaseEvidenceDetail.model_validate(evidence))

    async def list_response_actions(self, case_uid: str) -> list[ResponseActionDetail]:
        case = await self._get_case(case_uid)
        rows = (
            await self.session.scalars(
                select(ResponseAction)
                .where(ResponseAction.case_id == case.id)
                .order_by(ResponseAction.created_at.desc())
            )
        ).all()
        return [ResponseActionDetail.model_validate(row) for row in rows]

    async def execute_response_action(self, case_uid: str, payload: ResponseActionRequest) -> ResponseActionDetail:
        case = await self._get_case(case_uid)
        action = ResponseAction(
            case_id=case.id,
            alert_id=payload.alert_id,
            action_type=payload.action_type,
            target=payload.target,
            status=ResponseActionStatus.RUNNING,
            parameters=payload.parameters,
            result={},
        )
        self.session.add(action)
        await self.session.flush()

        handler = self.response_action_handlers.get(payload.action_type)
        result = (
            await handler.execute(
                {
                    "target": payload.target,
                    "parameters": payload.parameters,
                    "case_uid": case.case_uid,
                }
            )
            if handler is not None
            else {"status": "unsupported", "action": payload.action_type.value, "payload": payload.parameters}
        )
        action.result = result
        action.status = (
            ResponseActionStatus.COMPLETED if result.get("status") != "failed" else ResponseActionStatus.FAILED
        )

        await self._add_timeline_event(
            case.id,
            event_type=CaseEventType.RESPONSE_ACTION,
            actor=payload.actor,
            summary=f"Executed response action {payload.action_type.value}",
            details={"target": payload.target, "result": result},
        )
        await self.session.commit()
        return ResponseActionDetail.model_validate(action)

    async def run_playbook(self, case_uid: str, payload: PlaybookRunRequest) -> PlaybookRunResponse:
        case = await self._get_case(case_uid)
        playbook_id = payload.playbook_id or case.playbook_id
        if not playbook_id:
            raise HTTPException(status_code=400, detail="Case has no associated playbook")

        playbook = self.playbook_runner.load_playbook(playbook_id)
        alert = await self._select_playbook_alert(case.id, payload.alert_id)
        context = {
            "case": {
                "case_uid": case.case_uid,
                "title": case.title,
                "assigned_to": case.assigned_to,
            },
            "alert": {
                "source_ip": alert.source_ip if alert else None,
                "assigned_to": alert.assigned_to if alert else None,
                "title": alert.title if alert else None,
            },
            **payload.extra_context,
        }

        generated_timeline_ids: list[int] = []
        response_action_ids: list[int] = []
        for step in playbook.get("steps", []):
            step_type = step.get("type", "notify")
            if step_type == "action":
                target = self.playbook_runner.render_target(str(step.get("target", "")), context)
                action_detail = await self.execute_response_action(
                    case.case_uid,
                    ResponseActionRequest(
                        actor=payload.actor,
                        action_type=ResponseActionType(step["action"]),
                        target=target,
                        alert_id=payload.alert_id or (alert.id if alert else None),
                        parameters={"playbook_id": playbook_id},
                    ),
                )
                response_action_ids.append(action_detail.id)
                continue

            event = await self._add_timeline_event(
                case.id,
                event_type=CaseEventType.PLAYBOOK_STEP if step_type != "evidence" else CaseEventType.EVIDENCE_ADDED,
                actor=payload.actor,
                summary=str(step.get("summary", step_type)).strip() or step_type,
                details={"playbook_id": playbook_id, "step": step},
            )
            generated_timeline_ids.append(event.id)

        await self.session.commit()
        return PlaybookRunResponse(
            playbook_id=playbook_id,
            executed_steps=len(playbook.get("steps", [])),
            generated_timeline_ids=generated_timeline_ids,
            response_action_ids=response_action_ids,
        )

    async def _build_case_detail(self, case: Case) -> CaseDetail:
        alerts = (
            await self.session.execute(
                select(Alert)
                .join(CaseAlert, CaseAlert.alert_id == Alert.id)
                .where(CaseAlert.case_id == case.id)
                .order_by(Alert.created_at.desc())
            )
        ).scalars().all()
        timeline = (
            await self.session.scalars(
                select(CaseEvent).where(CaseEvent.case_id == case.id).order_by(CaseEvent.created_at.desc())
            )
        ).all()
        evidence = (
            await self.session.scalars(
                select(CaseEvidence).where(CaseEvidence.case_id == case.id).order_by(CaseEvidence.created_at.desc())
            )
        ).all()
        response_actions = (
            await self.session.scalars(
                select(ResponseAction)
                .where(ResponseAction.case_id == case.id)
                .order_by(ResponseAction.created_at.desc())
            )
        ).all()

        return CaseDetail(
            id=case.id,
            case_uid=case.case_uid,
            title=case.title,
            description=case.description,
            severity=case.severity,
            status=case.status,
            priority=case.priority,
            assigned_to=case.assigned_to,
            playbook_id=case.playbook_id,
            sla_due_at=case.sla_due_at,
            resolved_at=case.resolved_at,
            created_at=case.created_at,
            updated_at=case.updated_at,
            alerts=[
                CaseAlertSummary(
                    alert_uid=alert.alert_uid,
                    title=alert.title,
                    severity=alert.severity,
                    status=alert.status.value,
                )
                for alert in alerts
            ],
            timeline=[CaseEventDetail.model_validate(entry) for entry in timeline],
            evidence=[CaseEvidenceDetail.model_validate(item) for item in evidence],
            response_actions=[ResponseActionDetail.model_validate(item) for item in response_actions],
        )

    async def _select_playbook_alert(self, case_id: int, alert_id: int | None) -> Alert | None:
        if alert_id is not None:
            return await self.session.get(Alert, alert_id)

        return await self.session.scalar(
            select(Alert)
            .join(CaseAlert, CaseAlert.alert_id == Alert.id)
            .where(CaseAlert.case_id == case_id)
            .order_by(Alert.created_at.desc())
        )

    async def _get_case(self, case_uid: str) -> Case:
        case = await self.session.scalar(select(Case).where(Case.case_uid == case_uid))
        if case is None:
            raise HTTPException(status_code=404, detail="Case not found")
        return case

    async def _link_alert(self, case: Case, alert_id: int, actor: str) -> None:
        alert = await self.session.get(Alert, alert_id)
        if alert is None:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

        existing_link = await self.session.get(CaseAlert, {"case_id": case.id, "alert_id": alert.id})
        if existing_link is None:
            self.session.add(CaseAlert(case_id=case.id, alert_id=alert.id, created_at=utc_now()))

        alert.case_id = case.id
        alert.status = AlertStatus.INVESTIGATING
        await self._add_timeline_event(
            case.id,
            event_type=CaseEventType.ALERT_LINKED,
            actor=actor,
            summary=f"Linked alert {alert.alert_uid}",
            details={"alert_id": alert.id, "alert_uid": alert.alert_uid},
        )

    async def _add_timeline_event(
        self,
        case_id: int,
        event_type: CaseEventType,
        actor: str,
        summary: str,
        details: dict[str, object],
    ) -> CaseEvent:
        event = CaseEvent(
            case_id=case_id,
            event_type=event_type,
            actor=actor,
            summary=summary,
            details=details,
        )
        self.session.add(event)
        await self.session.flush()
        return event

    def _compute_sla_due_at(self, severity: SeverityLevel):
        acknowledgement_window, _ = SLA_WINDOWS[severity]
        return utc_now() + acknowledgement_window

    def _priority_for_severity(self, severity: SeverityLevel) -> int:
        return {
            SeverityLevel.CRITICAL: 1,
            SeverityLevel.HIGH: 2,
            SeverityLevel.MEDIUM: 3,
            SeverityLevel.LOW: 4,
        }[severity]