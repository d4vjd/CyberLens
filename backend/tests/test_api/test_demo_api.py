# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from datetime import UTC, datetime

from cyberlens.demo.router import get_demo_service
from cyberlens.demo.schemas import DemoCounts, DemoSeedResponse, DemoStatusResponse
from cyberlens.main import app
from cyberlens.settings.schemas import DemoSettings


class FakeDemoService:
    async def get_status(self):
        return DemoStatusResponse(
            demo=DemoSettings(
                enabled=True,
                intensity=6,
                mode="live",
                seeded_at=datetime(2026, 3, 12, 15, 0, tzinfo=UTC),
                generator_status="running",
            ),
            counts=DemoCounts(events=180, alerts=6, cases=3),
        )

    async def seed_dataset(self, payload):
        return DemoSeedResponse(
            seeded_events=payload.event_count or 180,
            generated_alerts=6,
            created_cases=3,
            seeded_at=datetime(2026, 3, 12, 15, 0, tzinfo=UTC),
            message="Seeded",
        )


async def override_demo_service():
    return FakeDemoService()


def test_demo_status_endpoint(client) -> None:
    app.dependency_overrides[get_demo_service] = override_demo_service
    response = client.get("/api/v1/demo/status")
    app.dependency_overrides.pop(get_demo_service, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["counts"]["cases"] == 3
    assert payload["demo"]["generator_status"] == "running"


def test_demo_seed_endpoint(client) -> None:
    app.dependency_overrides[get_demo_service] = override_demo_service
    response = client.post("/api/v1/demo/seed", json={"intensity": 5, "event_count": 200})
    app.dependency_overrides.pop(get_demo_service, None)

    assert response.status_code == 200
    assert response.json()["seeded_events"] == 200