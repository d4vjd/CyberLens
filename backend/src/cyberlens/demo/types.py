# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from cyberlens.ingestion.models import Event, SeverityLevel


@dataclass(slots=True)
class DemoEventSpec:
    timestamp: datetime
    event_type: str
    source_system: str
    raw_log: str
    severity: SeverityLevel = SeverityLevel.LOW
    source_ip: str | None = None
    dest_ip: str | None = None
    source_port: int | None = None
    dest_port: int | None = None
    protocol: str | None = None
    action: str | None = None
    hostname: str | None = None
    username: str | None = None
    message: str | None = None
    parsed_data: dict[str, Any] = field(default_factory=dict)
    is_demo: bool = True

    def to_event(self) -> Event:
        return Event(
            timestamp=self.timestamp,
            source_ip=self.source_ip,
            dest_ip=self.dest_ip,
            source_port=self.source_port,
            dest_port=self.dest_port,
            protocol=self.protocol,
            action=self.action,
            severity=self.severity,
            event_type=self.event_type,
            source_system=self.source_system,
            raw_log=self.raw_log,
            parsed_data=self.parsed_data,
            hostname=self.hostname,
            username=self.username,
            message=self.message,
            is_demo=self.is_demo,
        )
