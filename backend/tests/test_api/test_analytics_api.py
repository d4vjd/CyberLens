# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from datetime import UTC, datetime

from cyberlens.analytics.router import get_analytics_service
from cyberlens.analytics.schemas import (
    AnalyticsMetric,
    AnalyticsOverviewResponse,
    AnalyticsSourcePoint,
    AnalyticsTrendPoint,
)
from cyberlens.main import app


class FakeAnalyticsService:
    async def overview(self):
        return AnalyticsOverviewResponse(
            metrics=[
                AnalyticsMetric(label="Indexed events", value="120", delta="Latest window"),
                AnalyticsMetric(label="Alert volume", value="4", delta="Latest detections"),
                AnalyticsMetric(label="Tracked cases", value="2", delta="Incident load"),
            ],
            trends=[
                AnalyticsTrendPoint(bucket="2026-03-12 10:00", events=15, alerts=1),
                AnalyticsTrendPoint(bucket="2026-03-12 11:00", events=22, alerts=2),
            ],
            top_sources=[
                AnalyticsSourcePoint(
                    source_ip="198.51.100.42",
                    event_count=12,
                    alert_count=2,
                    last_seen=datetime(2026, 3, 12, 11, 15, tzinfo=UTC),
                )
            ],
        )


async def override_analytics_service():
    return FakeAnalyticsService()


def test_analytics_overview_endpoint(client) -> None:
    app.dependency_overrides[get_analytics_service] = override_analytics_service
    response = client.get("/api/v1/analytics/overview")
    app.dependency_overrides.pop(get_analytics_service, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["metrics"][0]["label"] == "Indexed events"
    assert payload["top_sources"][0]["source_ip"] == "198.51.100.42"
