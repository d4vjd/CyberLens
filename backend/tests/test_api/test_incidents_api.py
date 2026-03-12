# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from datetime import UTC, datetime

from cyberlens.incidents.models import (
    CaseEventType,
    CaseStatus,
    ResponseActionStatus,
    ResponseActionType,
)
from cyberlens.incidents.router import get_incident_service
from cyberlens.incidents.schemas import (
    CaseAlertSummary,
    CaseDetail,
    CaseEventDetail,
    CaseEvidenceDetail,
    CaseListResponse,
    CaseSummary,
    PlaybookRunResponse,
    ResponseActionDetail,
)
from cyberlens.ingestion.models import SeverityLevel
from cyberlens.main import app


def build_case_detail(case_uid: str = "case-001") -> CaseDetail:
    return CaseDetail(
        id=1,
        case_uid=case_uid,
        title="DEMO: SSH Brute Force Investigation",
        description="Created from alert",
        severity=SeverityLevel.HIGH,
        status=CaseStatus.IN_PROGRESS,
        priority=2,
        assigned_to="ahassan",
        playbook_id="brute_force_response",
        sla_due_at=datetime(2026, 3, 12, 18, 0, tzinfo=UTC),
        resolved_at=None,
        created_at=datetime(2026, 3, 12, 16, 0, tzinfo=UTC),
        updated_at=datetime(2026, 3, 12, 16, 30, tzinfo=UTC),
        alerts=[
            CaseAlertSummary(
                alert_uid="alert-001",
                title="SSH Brute Force Attempt",
                severity=SeverityLevel.HIGH,
                status="investigating",
            )
        ],
        timeline=[
            CaseEventDetail(
                id=1,
                event_type=CaseEventType.COMMENT,
                actor="ahassan",
                summary="Case created",
                details={"source": "test"},
                created_at=datetime(2026, 3, 12, 16, 0, tzinfo=UTC),
            )
        ],
        evidence=[
            CaseEvidenceDetail(
                id=1,
                filename="auth-log.txt",
                file_path="/tmp/auth-log.txt",
                file_size=512,
                content_type="text/plain",
                created_at=datetime(2026, 3, 12, 16, 5, tzinfo=UTC),
            )
        ],
        response_actions=[
            ResponseActionDetail(
                id=1,
                action_type=ResponseActionType.BLOCK_IP,
                target="198.51.100.42",
                status=ResponseActionStatus.COMPLETED,
                parameters={},
                result={"status": "simulated"},
                created_at=datetime(2026, 3, 12, 16, 10, tzinfo=UTC),
            )
        ],
    )


class FakeIncidentService:
    async def list_cases(self):
        return CaseListResponse(
            items=[
                CaseSummary(
                    id=1,
                    case_uid="case-001",
                    title="DEMO: SSH Brute Force Investigation",
                    severity=SeverityLevel.HIGH,
                    status=CaseStatus.IN_PROGRESS,
                    priority=2,
                    assigned_to="ahassan",
                    playbook_id="brute_force_response",
                    sla_due_at=datetime(2026, 3, 12, 18, 0, tzinfo=UTC),
                    alert_count=1,
                    evidence_count=1,
                    created_at=datetime(2026, 3, 12, 16, 0, tzinfo=UTC),
                )
            ],
            total=1,
        )

    async def get_case(self, case_uid: str):
        return build_case_detail(case_uid)

    async def create_case_from_alert(self, alert_id: int, payload):
        del alert_id, payload
        return build_case_detail()

    async def add_comment(self, case_uid: str, payload):
        del case_uid, payload
        return build_case_detail().timeline[0]

    async def run_playbook(self, case_uid: str, payload):
        del case_uid, payload
        return PlaybookRunResponse(
            playbook_id="brute_force_response",
            executed_steps=2,
            generated_timeline_ids=[1],
            response_action_ids=[1],
        )


async def override_incident_service():
    return FakeIncidentService()


def test_list_incidents_endpoint(client) -> None:
    app.dependency_overrides[get_incident_service] = override_incident_service
    response = client.get("/api/v1/incidents")
    app.dependency_overrides.pop(get_incident_service, None)

    assert response.status_code == 200
    assert response.json()["items"][0]["case_uid"] == "case-001"


def test_create_case_from_alert_endpoint(client) -> None:
    app.dependency_overrides[get_incident_service] = override_incident_service
    response = client.post("/api/v1/incidents/from-alerts/1", json={"actor": "ahassan"})
    app.dependency_overrides.pop(get_incident_service, None)

    assert response.status_code == 200
    assert response.json()["title"] == "DEMO: SSH Brute Force Investigation"
