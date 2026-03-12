# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from cyberlens.detection.models import AlertStatus, RuleType
from cyberlens.ingestion.models import SeverityLevel


class RuleSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rule_id: str
    title: str
    description: str | None = None
    severity: SeverityLevel
    rule_type: RuleType
    mitre_tactic: str | None
    mitre_technique_id: str | None
    enabled: bool
    historical_matches: int = 0
    last_triggered_at: datetime | None = None


class AlertDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alert_uid: str
    title: str
    severity: SeverityLevel
    status: AlertStatus
    source_ip: str | None
    mitre_tactic: str | None
    mitre_technique_id: str | None
    matched_events: list[dict[str, Any]]
    assigned_to: str | None
    created_at: datetime
    rule_id: int


class AlertListResponse(BaseModel):
    items: list[AlertDetail]
    total: int
    offset: int
    limit: int


class RuleSyncResponse(BaseModel):
    loaded_count: int
    loaded_rule_ids: list[str]


class RuleMutationRequest(BaseModel):
    yaml: str = Field(min_length=1)


class RuleMutationResponse(BaseModel):
    rule_id: str
    title: str
    file_path: str
    enabled: bool
    message: str


class RuleHistoricalTestRequest(BaseModel):
    yaml: str = Field(min_length=1)
    limit: int = Field(default=500, ge=1, le=5000)


class RuleHistoricalTestResponse(BaseModel):
    rule_id: str
    title: str
    evaluated_events: int
    generated_alerts: int
    sample_event_ids: list[int]
    sample_matches: list[dict[str, Any]]