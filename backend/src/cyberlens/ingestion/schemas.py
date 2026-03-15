# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from cyberlens.ingestion.models import SeverityLevel


class IngestSingleRequest(BaseModel):
    raw_log: str = Field(min_length=1)
    source_system: str | None = None
    source_type: str | None = None
    received_at: datetime | None = None
    is_demo: bool = False


class IngestBatchRequest(BaseModel):
    logs: list[IngestSingleRequest] = Field(min_length=1, max_length=2000)


class IngestedEventSummary(BaseModel):
    id: int
    timestamp: datetime
    event_type: str
    source_system: str
    parser_name: str


class IngestResponse(BaseModel):
    ingested_count: int
    parser_counts: dict[str, int]
    events: list[IngestedEventSummary]


class BaselineEmitterStatus(BaseModel):
    running: bool = False
    pipeline: str = "live_ingestion"
    emitted_batches: int = 0
    emitted_events: int = 0
    last_batch_size: int = 0
    last_emit_at: datetime | None = None
    last_ingested_at: datetime | None = None
    event_mix: dict[str, int] = Field(default_factory=dict)
    parser_mix: dict[str, int] = Field(default_factory=dict)
    last_checks: dict[str, str] = Field(default_factory=dict)
    monitored_services: list[str] = Field(default_factory=list)
    last_error: str | None = None


class EventDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    source_ip: str | None
    dest_ip: str | None
    source_port: int | None
    dest_port: int | None
    protocol: str | None
    action: str | None
    severity: SeverityLevel
    event_type: str
    source_system: str
    raw_log: str
    parsed_data: dict[str, Any]
    hostname: str | None
    username: str | None
    message: str | None
    is_demo: bool


class EventListResponse(BaseModel):
    items: list[EventDetail]
    total: int
    offset: int
    limit: int


class EventQueryParams(BaseModel):
    offset: int = 0
    limit: int = 50
    event_type: str | None = None
    severity: str | None = None
    source_ip: str | None = None
    dest_ip: str | None = None
    source_system: str | None = None
    action: str | None = None
    search: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None

    @field_validator("severity")
    @classmethod
    def normalize_severity(cls, value: str | None) -> str | None:
        return value.lower() if value else value
