# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from datetime import UTC, datetime

from cyberlens.ingestion.router import get_ingestion_service
from cyberlens.ingestion.schemas import EventDetail, EventListResponse, IngestResponse, IngestedEventSummary
from cyberlens.ingestion.models import SeverityLevel
from cyberlens.main import app


class FakeIngestionService:
    async def ingest_batch(self, payloads):
        return IngestResponse(
            ingested_count=len(payloads),
            parser_counts={"syslog": len(payloads)},
            events=[
                IngestedEventSummary(
                    id=1,
                    timestamp=datetime(2026, 3, 12, 16, 12, 4, tzinfo=UTC),
                    event_type="authentication",
                    source_system="sshd",
                    parser_name="syslog",
                )
            ],
        )

    async def list_events(self, params):
        return EventListResponse(
            items=[
                EventDetail(
                    id=1,
                    timestamp=datetime(2026, 3, 12, 16, 12, 4, tzinfo=UTC),
                    source_ip="198.51.100.24",
                    dest_ip="10.0.0.10",
                    source_port=55122,
                    dest_port=22,
                    protocol="tcp",
                    action="failed",
                    severity=SeverityLevel.HIGH,
                    event_type="authentication",
                    source_system="sshd",
                    raw_log="failed password",
                    parsed_data={"event_type": "authentication"},
                    hostname="web-prod-01",
                    username="admin",
                    message="Failed password for invalid user admin",
                    is_demo=False,
                )
            ],
            total=1,
            offset=params.offset,
            limit=params.limit,
        )

    async def get_event(self, event_id: int):
        return EventDetail(
            id=event_id,
            timestamp=datetime(2026, 3, 12, 16, 12, 4, tzinfo=UTC),
            source_ip="198.51.100.24",
            dest_ip="10.0.0.10",
            source_port=55122,
            dest_port=22,
            protocol="tcp",
            action="failed",
            severity=SeverityLevel.HIGH,
            event_type="authentication",
            source_system="sshd",
            raw_log="failed password",
            parsed_data={"event_type": "authentication"},
            hostname="web-prod-01",
            username="admin",
            message="Failed password for invalid user admin",
            is_demo=False,
        )


async def override_ingestion_service():
    return FakeIngestionService()


def test_ingest_raw_endpoint(client) -> None:
    app.dependency_overrides[get_ingestion_service] = override_ingestion_service
    response = client.post(
        "/api/v1/ingest/raw",
        json={"raw_log": "<34>1 2026-03-12T16:12:04Z web sshd 1 - - Failed password"},
    )
    app.dependency_overrides.pop(get_ingestion_service, None)

    assert response.status_code == 200
    assert response.json()["ingested_count"] == 1
    assert response.json()["parser_counts"] == {"syslog": 1}


def test_list_events_endpoint(client) -> None:
    app.dependency_overrides[get_ingestion_service] = override_ingestion_service
    response = client.get("/api/v1/events?limit=10&offset=0")
    app.dependency_overrides.pop(get_ingestion_service, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["event_type"] == "authentication"