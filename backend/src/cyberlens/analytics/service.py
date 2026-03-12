# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cyberlens.analytics.schemas import AnalyticsMetric, AnalyticsOverviewResponse, AnalyticsSourcePoint, AnalyticsTrendPoint
from cyberlens.detection.models import Alert
from cyberlens.incidents.models import Case
from cyberlens.ingestion.models import Event


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def overview(self) -> AnalyticsOverviewResponse:
        events = (await self.session.scalars(select(Event).order_by(Event.timestamp.desc()).limit(500))).all()
        alerts = (await self.session.scalars(select(Alert).order_by(Alert.created_at.desc()).limit(200))).all()
        cases = (await self.session.scalars(select(Case).order_by(Case.created_at.desc()).limit(100))).all()

        trend_map: dict[str, dict[str, int]] = defaultdict(lambda: {"events": 0, "alerts": 0})
        source_map: dict[str, dict[str, object]] = defaultdict(
            lambda: {"event_count": 0, "alert_count": 0, "last_seen": None}
        )

        for event in events:
            bucket = event.timestamp.strftime("%Y-%m-%d %H:00")
            trend_map[bucket]["events"] += 1
            source = event.source_ip or event.hostname or "unknown"
            source_map[source]["event_count"] = int(source_map[source]["event_count"]) + 1
            source_map[source]["last_seen"] = event.timestamp

        for alert in alerts:
            bucket = alert.created_at.strftime("%Y-%m-%d %H:00")
            trend_map[bucket]["alerts"] += 1
            source = alert.source_ip or "unknown"
            source_map[source]["alert_count"] = int(source_map[source]["alert_count"]) + 1
            source_map[source]["last_seen"] = alert.created_at

        top_sources = sorted(
            [
                AnalyticsSourcePoint(
                    source_ip=source,
                    event_count=int(values["event_count"]),
                    alert_count=int(values["alert_count"]),
                    last_seen=values["last_seen"],
                )
                for source, values in source_map.items()
            ],
            key=lambda item: (item.alert_count, item.event_count),
            reverse=True,
        )[:10]

        return AnalyticsOverviewResponse(
            metrics=[
                AnalyticsMetric(label="Indexed events", value=str(len(events)), delta="Latest 500 from event store"),
                AnalyticsMetric(label="Alert volume", value=str(len(alerts)), delta="Latest 200 detections"),
                AnalyticsMetric(label="Tracked cases", value=str(len(cases)), delta="Incident workspace load"),
            ],
            trends=[
                AnalyticsTrendPoint(bucket=bucket, events=value["events"], alerts=value["alerts"])
                for bucket, value in sorted(trend_map.items())[-12:]
            ],
            top_sources=top_sources,
        )