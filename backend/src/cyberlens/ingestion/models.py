# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from cyberlens.db.base import Base, TimestampMixin
from cyberlens.db.enums import enum_column


class SeverityLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Event(Base, TimestampMixin):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    timestamp: Mapped[Any] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    source_ip: Mapped[str | None] = mapped_column(String(64), index=True)
    dest_ip: Mapped[str | None] = mapped_column(String(64), index=True)
    source_port: Mapped[int | None] = mapped_column(Integer)
    dest_port: Mapped[int | None] = mapped_column(Integer)
    protocol: Mapped[str | None] = mapped_column(String(16))
    action: Mapped[str | None] = mapped_column(String(64))
    severity: Mapped[SeverityLevel] = mapped_column(
        enum_column(SeverityLevel),
        default=SeverityLevel.MEDIUM,
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_system: Mapped[str] = mapped_column(String(128), nullable=False)
    raw_log: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    hostname: Mapped[str | None] = mapped_column(String(255))
    username: Mapped[str | None] = mapped_column(String(255))
    message: Mapped[str | None] = mapped_column(Text)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
