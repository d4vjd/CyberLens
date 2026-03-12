# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AnalyticsMetric(BaseModel):
    label: str
    value: str
    delta: str


class AnalyticsTrendPoint(BaseModel):
    bucket: str
    events: int
    alerts: int


class AnalyticsSourcePoint(BaseModel):
    source_ip: str
    event_count: int
    alert_count: int
    last_seen: datetime | None


class AnalyticsOverviewResponse(BaseModel):
    metrics: list[AnalyticsMetric]
    trends: list[AnalyticsTrendPoint]
    top_sources: list[AnalyticsSourcePoint]