# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from cyberlens.db.base import Base, TimestampMixin
from cyberlens.db.enums import enum_column
from cyberlens.ingestion.models import SeverityLevel


class CaseStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class CaseEventType(StrEnum):
    COMMENT = "comment"
    STATUS_CHANGE = "status_change"
    ASSIGNMENT = "assignment"
    ALERT_LINKED = "alert_linked"
    EVIDENCE_ADDED = "evidence_added"
    PLAYBOOK_STEP = "playbook_step"
    RESPONSE_ACTION = "response_action"
    ESCALATION = "escalation"


class ResponseActionType(StrEnum):
    BLOCK_IP = "block_ip"
    ISOLATE_HOST = "isolate_host"
    DISABLE_ACCOUNT = "disable_account"
    CUSTOM = "custom"


class ResponseActionStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Case(Base, TimestampMixin):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_uid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[SeverityLevel] = mapped_column(enum_column(SeverityLevel), nullable=False)
    status: Mapped[CaseStatus] = mapped_column(
        enum_column(CaseStatus),
        default=CaseStatus.OPEN,
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    assigned_to: Mapped[str | None] = mapped_column(String(255))
    playbook_id: Mapped[str | None] = mapped_column(String(128))
    sla_due_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CaseEvent(Base, TimestampMixin):
    __tablename__ = "case_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), nullable=False)
    event_type: Mapped[CaseEventType] = mapped_column(
        enum_column(CaseEventType),
        nullable=False,
    )
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class CaseAlert(Base):
    __tablename__ = "case_alerts"

    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"), primary_key=True)
    created_at: Mapped[Any] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class CaseEvidence(Base, TimestampMixin):
    __tablename__ = "case_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)


class ResponseAction(Base, TimestampMixin):
    __tablename__ = "response_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[int | None] = mapped_column(ForeignKey("cases.id"))
    alert_id: Mapped[int | None] = mapped_column(ForeignKey("alerts.id"))
    action_type: Mapped[ResponseActionType] = mapped_column(
        enum_column(ResponseActionType),
        nullable=False,
    )
    target: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ResponseActionStatus] = mapped_column(
        enum_column(ResponseActionStatus),
        default=ResponseActionStatus.PENDING,
        nullable=False,
    )
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    result: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
