# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from enum import StrEnum
from typing import Any

from sqlalchemy import Boolean, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from cyberlens.db.base import Base, TimestampMixin
from cyberlens.db.enums import enum_column


class AnalystRole(StrEnum):
    SOC_ANALYST = "soc_analyst"
    VULNERABILITY_ANALYST = "vulnerability_analyst"
    INCIDENT_COMMANDER = "incident_commander"
    ADMIN = "admin"


class Analyst(Base, TimestampMixin):
    __tablename__ = "analysts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[AnalystRole] = mapped_column(enum_column(AnalystRole), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class SystemConfig(Base, TimestampMixin):
    __tablename__ = "system_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    config_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    config_value: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))