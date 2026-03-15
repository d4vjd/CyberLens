# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from cyberlens.settings.schemas import DemoSettings


class DemoCounts(BaseModel):
    events: int
    alerts: int
    cases: int


class DemoStatusResponse(BaseModel):
    demo: DemoSettings
    counts: DemoCounts


class DemoSeedRequest(BaseModel):
    days: int = Field(default=7, ge=1, le=30)
    intensity: int = Field(default=5, ge=1, le=10)
    event_count: int | None = Field(default=None, ge=50, le=10000)
    force: bool = False


class DemoSeedResponse(BaseModel):
    seeded_events: int
    generated_alerts: int
    created_cases: int
    seeded_at: datetime
    skipped: bool = False
    message: str


class DataClearResponse(BaseModel):
    scope: str
    cleared_events: int
    cleared_alerts: int
    cleared_cases: int
    message: str


class DemoGeneratorRequest(BaseModel):
    intensity: int = Field(default=5, ge=1, le=10)
