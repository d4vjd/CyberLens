# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from cyberlens.incidents.models import CaseEventType, CaseStatus, ResponseActionStatus, ResponseActionType
from cyberlens.ingestion.models import SeverityLevel


class CaseAlertSummary(BaseModel):
    alert_uid: str
    title: str
    severity: SeverityLevel
    status: str


class CaseEvidenceDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_path: str
    file_size: int
    content_type: str
    created_at: datetime


class ResponseActionDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action_type: ResponseActionType
    target: str
    status: ResponseActionStatus
    parameters: dict[str, Any]
    result: dict[str, Any]
    created_at: datetime


class CaseEventDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: CaseEventType
    actor: str
    summary: str
    details: dict[str, Any]
    created_at: datetime


class CaseDetail(BaseModel):
    id: int
    case_uid: str
    title: str
    description: str | None
    severity: SeverityLevel
    status: CaseStatus
    priority: int
    assigned_to: str | None
    playbook_id: str | None
    sla_due_at: datetime | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime
    alerts: list[CaseAlertSummary]
    timeline: list[CaseEventDetail]
    evidence: list[CaseEvidenceDetail]
    response_actions: list[ResponseActionDetail]


class CaseSummary(BaseModel):
    id: int
    case_uid: str
    title: str
    severity: SeverityLevel
    status: CaseStatus
    priority: int
    assigned_to: str | None
    playbook_id: str | None
    sla_due_at: datetime | None
    alert_count: int
    evidence_count: int
    created_at: datetime


class CaseListResponse(BaseModel):
    items: list[CaseSummary]
    total: int


class CaseCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str | None = None
    severity: SeverityLevel
    priority: int = Field(default=3, ge=1, le=5)
    assigned_to: str | None = None
    playbook_id: str | None = None
    alert_ids: list[int] = Field(default_factory=list)
    actor: str = "system"


class CaseUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    severity: SeverityLevel | None = None
    status: CaseStatus | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    assigned_to: str | None = None
    playbook_id: str | None = None
    actor: str = "system"


class CaseCommentRequest(BaseModel):
    actor: str = Field(default="analyst", min_length=1)
    summary: str = Field(min_length=3, max_length=255)
    details: dict[str, Any] = Field(default_factory=dict)


class CaseFromAlertRequest(BaseModel):
    actor: str = "system"
    assigned_to: str | None = None
    playbook_id: str | None = None
    title: str | None = None


class ResponseActionRequest(BaseModel):
    actor: str = "system"
    action_type: ResponseActionType
    target: str
    alert_id: int | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class PlaybookRunRequest(BaseModel):
    actor: str = "system"
    playbook_id: str | None = None
    alert_id: int | None = None
    extra_context: dict[str, Any] = Field(default_factory=dict)


class PlaybookRunResponse(BaseModel):
    playbook_id: str
    executed_steps: int
    generated_timeline_ids: list[int]
    response_action_ids: list[int]


class EvidenceUploadResponse(BaseModel):
    evidence: CaseEvidenceDetail