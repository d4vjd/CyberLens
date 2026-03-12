# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cyberlens.analytics.schemas import (
    AnalyticsMetric,
    AnalyticsOverviewResponse,
    AnalyticsSourcePoint,
    AnalyticsTrendPoint,
)
from cyberlens.detection.models import Alert
from cyberlens.incidents.models import Case
from cyberlens.ingestion.models import Event


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def overview(self) -> AnalyticsOverviewResponse:
        events = (
            await self.session.scalars(select(Event).order_by(Event.timestamp.desc()).limit(500))
        ).all()
        alerts = (
            await self.session.scalars(select(Alert).order_by(Alert.created_at.desc()).limit(200))
        ).all()
        cases = (
            await self.session.scalars(select(Case).order_by(Case.created_at.desc()).limit(100))
        ).all()

        trend_map: dict[str, dict[str, int]] = defaultdict(lambda: {"events": 0, "alerts": 0})

        event_counts: dict[str, int] = defaultdict(int)
        alert_counts: dict[str, int] = defaultdict(int)
        last_seen_map: dict[str, datetime | None] = {}

        for event in events:
            bucket = event.timestamp.strftime("%Y-%m-%d %H:00")
            trend_map[bucket]["events"] += 1
            source = event.source_ip or event.hostname or "unknown"
            event_counts[source] += 1
            last_seen_map[source] = event.timestamp

        for alert in alerts:
            bucket = alert.created_at.strftime("%Y-%m-%d %H:00")
            trend_map[bucket]["alerts"] += 1
            source = alert.source_ip or "unknown"
            alert_counts[source] += 1
            last_seen_map[source] = alert.created_at

        all_sources = set(event_counts) | set(alert_counts)
        top_sources = sorted(
            [
                AnalyticsSourcePoint(
                    source_ip=source,
                    event_count=event_counts[source],
                    alert_count=alert_counts[source],
                    last_seen=last_seen_map.get(source),
                )
                for source in all_sources
            ],
            key=lambda item: (item.alert_count, item.event_count),
            reverse=True,
        )[:10]

        return AnalyticsOverviewResponse(
            metrics=[
                AnalyticsMetric(
                    label="Indexed events",
                    value=str(len(events)),
                    delta="Latest 500 from event store",
                ),
                AnalyticsMetric(
                    label="Alert volume", value=str(len(alerts)), delta="Latest 200 detections"
                ),
                AnalyticsMetric(
                    label="Tracked cases", value=str(len(cases)), delta="Incident workspace load"
                ),
            ],
            trends=[
                AnalyticsTrendPoint(bucket=bucket, events=value["events"], alerts=value["alerts"])
                for bucket, value in sorted(trend_map.items())[-12:]
            ],
            top_sources=top_sources,
        )
