# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from datetime import UTC, datetime

from cyberlens.detection.router import get_detection_service
from cyberlens.detection.schemas import (
    AlertDetail,
    AlertListResponse,
    RuleHistoricalTestResponse,
    RuleMutationResponse,
    RuleSummary,
)
from cyberlens.detection.models import AlertStatus, RuleType
from cyberlens.ingestion.models import SeverityLevel
from cyberlens.main import app


class FakeDetectionService:
    async def list_rules(self):
        return [
            RuleSummary(
                id=1,
                rule_id="brute_force_ssh",
                title="SSH Brute Force Attempt",
                description="Detects repeated failed SSH authentication attempts.",
                severity=SeverityLevel.HIGH,
                rule_type=RuleType.THRESHOLD,
                mitre_tactic="credential-access",
                mitre_technique_id="T1110.001",
                enabled=True,
                historical_matches=3,
                last_triggered_at=datetime(2026, 3, 12, 16, 30, tzinfo=UTC),
            )
        ]

    async def list_alerts(self, offset: int, limit: int):
        return AlertListResponse(
            items=[
                AlertDetail(
                    id=1,
                    alert_uid="alert-1",
                    title="SSH Brute Force Attempt",
                    severity=SeverityLevel.HIGH,
                    status=AlertStatus.NEW,
                    source_ip="198.51.100.24",
                    mitre_tactic="credential-access",
                    mitre_technique_id="T1110.001",
                    matched_events=[{"id": 10}],
                    assigned_to=None,
                    created_at=datetime(2026, 3, 12, 16, 30, tzinfo=UTC),
                    rule_id=1,
                )
            ],
            total=1,
            offset=offset,
            limit=limit,
        )

    async def get_alert(self, alert_id: int):
        return AlertDetail(
            id=alert_id,
            alert_uid="alert-1",
            title="SSH Brute Force Attempt",
            severity=SeverityLevel.HIGH,
            status=AlertStatus.NEW,
            source_ip="198.51.100.24",
            mitre_tactic="credential-access",
            mitre_technique_id="T1110.001",
            matched_events=[{"id": 10}],
            assigned_to=None,
            created_at=datetime(2026, 3, 12, 16, 30, tzinfo=UTC),
            rule_id=1,
        )

    async def save_rule_yaml(self, yaml_content: str):
        assert "brute_force_ssh" in yaml_content
        return RuleMutationResponse(
            rule_id="brute_force_ssh",
            title="SSH Brute Force Attempt",
            file_path="/tmp/brute_force_ssh.yml",
            enabled=True,
            message="saved",
        )

    async def retire_rule(self, rule_id: str):
        return RuleMutationResponse(
            rule_id=rule_id,
            title="SSH Brute Force Attempt",
            file_path="/tmp/brute_force_ssh.yml",
            enabled=False,
            message="retired",
        )

    async def test_rule_yaml(self, yaml_content: str, limit: int):
        assert "brute_force_ssh" in yaml_content
        assert limit == 250
        return RuleHistoricalTestResponse(
            rule_id="brute_force_ssh",
            title="SSH Brute Force Attempt",
            evaluated_events=250,
            generated_alerts=4,
            sample_event_ids=[101, 102],
            sample_matches=[{"id": 101, "event_type": "authentication"}],
        )


async def override_detection_service():
    return FakeDetectionService()


def test_list_rules_endpoint(client) -> None:
    app.dependency_overrides[get_detection_service] = override_detection_service
    response = client.get("/api/v1/rules")
    app.dependency_overrides.pop(get_detection_service, None)

    assert response.status_code == 200
    assert response.json()[0]["rule_id"] == "brute_force_ssh"
    assert response.json()[0]["historical_matches"] == 3


def test_list_alerts_endpoint(client) -> None:
    app.dependency_overrides[get_detection_service] = override_detection_service
    response = client.get("/api/v1/alerts")
    app.dependency_overrides.pop(get_detection_service, None)

    assert response.status_code == 200
    assert response.json()["items"][0]["mitre_technique_id"] == "T1110.001"


def test_save_rule_endpoint(client) -> None:
    app.dependency_overrides[get_detection_service] = override_detection_service
    response = client.post(
        "/api/v1/rules",
        json={"yaml": "id: brute_force_ssh\ntitle: SSH Brute Force Attempt\nseverity: high\ntype: threshold\ndetection: {}"},
    )
    app.dependency_overrides.pop(get_detection_service, None)

    assert response.status_code == 200
    assert response.json()["file_path"] == "/tmp/brute_force_ssh.yml"


def test_rule_historical_test_endpoint(client) -> None:
    app.dependency_overrides[get_detection_service] = override_detection_service
    response = client.post(
        "/api/v1/rules/test",
        json={
            "yaml": "id: brute_force_ssh\ntitle: SSH Brute Force Attempt\nseverity: high\ntype: threshold\ndetection: {}",
            "limit": 250,
        },
    )
    app.dependency_overrides.pop(get_detection_service, None)

    assert response.status_code == 200
    assert response.json()["generated_alerts"] == 4


def test_retire_rule_endpoint(client) -> None:
    app.dependency_overrides[get_detection_service] = override_detection_service
    response = client.delete("/api/v1/rules/brute_force_ssh")
    app.dependency_overrides.pop(get_detection_service, None)

    assert response.status_code == 200
    assert response.json()["enabled"] is False