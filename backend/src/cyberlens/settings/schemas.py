# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from cyberlens.settings.models import AnalystRole


class AnalystSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    display_name: str
    role: AnalystRole
    email: str
    is_active: bool
    active_cases: int = 0


class DemoSettings(BaseModel):
    enabled: bool = False
    intensity: int = Field(default=5, ge=1, le=10)
    mode: str = "live"
    seeded_at: datetime | None = None
    generator_status: str = "stopped"


class DemoSettingsUpdate(BaseModel):
    enabled: bool | None = None
    intensity: int | None = Field(default=None, ge=1, le=10)
    mode: str | None = None


class SystemConfigItem(BaseModel):
    key: str
    value: dict[str, object]
    description: str | None = None


class SettingsStatusResponse(BaseModel):
    analysts: list[AnalystSummary]
    demo: DemoSettings
    configs: list[SystemConfigItem]
