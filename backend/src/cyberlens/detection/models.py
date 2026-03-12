# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from enum import StrEnum
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cyberlens.db.base import Base, TimestampMixin
from cyberlens.db.enums import enum_column
from cyberlens.ingestion.models import SeverityLevel


class RuleType(StrEnum):
    THRESHOLD = "threshold"
    PATTERN = "pattern"
    SEQUENCE = "sequence"
    AGGREGATION = "aggregation"


class AlertStatus(StrEnum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class DetectionRule(Base, TimestampMixin):
    __tablename__ = "detection_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rule_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[SeverityLevel] = mapped_column(enum_column(SeverityLevel), nullable=False)
    rule_type: Mapped[RuleType] = mapped_column(enum_column(RuleType), nullable=False)
    rule_definition: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    mitre_tactic: Mapped[str | None] = mapped_column(String(128))
    mitre_technique_id: Mapped[str | None] = mapped_column(String(32))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_uid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    rule_id: Mapped[int] = mapped_column(ForeignKey("detection_rules.id"), nullable=False)
    case_id: Mapped[int | None] = mapped_column(ForeignKey("cases.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[SeverityLevel] = mapped_column(enum_column(SeverityLevel), nullable=False)
    status: Mapped[AlertStatus] = mapped_column(
        enum_column(AlertStatus),
        default=AlertStatus.NEW,
        nullable=False,
    )
    source_ip: Mapped[str | None] = mapped_column(String(64))
    mitre_tactic: Mapped[str | None] = mapped_column(String(128))
    mitre_technique_id: Mapped[str | None] = mapped_column(String(32))
    matched_events: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    assigned_to: Mapped[str | None] = mapped_column(String(255))

    rule: Mapped["DetectionRule"] = relationship()


class MitreTechniqueCoverage(Base, TimestampMixin):
    __tablename__ = "mitre_technique_coverage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    technique_id: Mapped[str] = mapped_column(String(32), nullable=False)
    tactic: Mapped[str] = mapped_column(String(128), nullable=False)
    rule_id: Mapped[int] = mapped_column(ForeignKey("detection_rules.id"), nullable=False)
    alert_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_alert_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)