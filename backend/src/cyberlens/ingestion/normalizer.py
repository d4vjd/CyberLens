# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from cyberlens.common.time_utils import utc_now
from cyberlens.ingestion.models import Event, SeverityLevel
from cyberlens.ingestion.schemas import IngestSingleRequest

SEVERITY_ALIASES = {
    "low": SeverityLevel.LOW,
    "informational": SeverityLevel.LOW,
    "info": SeverityLevel.LOW,
    "notice": SeverityLevel.LOW,
    "debug": SeverityLevel.LOW,
    "warning": SeverityLevel.MEDIUM,
    "warn": SeverityLevel.MEDIUM,
    "medium": SeverityLevel.MEDIUM,
    "error": SeverityLevel.HIGH,
    "high": SeverityLevel.HIGH,
    "err": SeverityLevel.HIGH,
    "critical": SeverityLevel.CRITICAL,
    "crit": SeverityLevel.CRITICAL,
    "alert": SeverityLevel.CRITICAL,
    "emergency": SeverityLevel.CRITICAL,
}


def normalize_timestamp(raw: Any, fallback: datetime | None = None) -> datetime:
    if isinstance(raw, datetime):
        dt = raw
    elif isinstance(raw, str):
        candidate = raw.strip()
        if candidate.endswith("Z"):
            candidate = candidate[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(candidate)
        except ValueError:
            dt = fallback or utc_now()
    else:
        dt = fallback or utc_now()

    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _first_value(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = payload.get(key)
        if value not in (None, "", []):
            return value
    return None


def _as_int(raw: Any) -> int | None:
    if raw in (None, ""):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _normalize_severity(raw: Any) -> SeverityLevel:
    if isinstance(raw, SeverityLevel):
        return raw
    if isinstance(raw, int):
        if raw >= 5:
            return SeverityLevel.CRITICAL
        if raw >= 4:
            return SeverityLevel.HIGH
        if raw >= 3:
            return SeverityLevel.MEDIUM
        return SeverityLevel.LOW
    if isinstance(raw, str):
        normalized = raw.strip().lower()
        return SEVERITY_ALIASES.get(normalized, SeverityLevel.MEDIUM)
    return SeverityLevel.MEDIUM


def normalize_event(
    payload: IngestSingleRequest,
    parsed: dict[str, Any],
    parser_name: str,
) -> Event:
    source_system = payload.source_system or _first_value(
        parsed,
        "source_system",
        "vendor",
        "channel",
        "parser",
    )
    message = _first_value(parsed, "message", "msg", "summary", "raw_message")
    hostname = _first_value(parsed, "hostname", "host", "computer_name")
    username = _first_value(parsed, "username", "user", "account_name")
    source_ip = _first_value(parsed, "source_ip", "src_ip", "client_ip", "ip")
    dest_ip = _first_value(parsed, "dest_ip", "dst_ip", "server_ip", "destination_ip")
    source_port = _as_int(_first_value(parsed, "source_port", "src_port", "sport"))
    dest_port = _as_int(_first_value(parsed, "dest_port", "dst_port", "dport", "port"))
    protocol = _first_value(parsed, "protocol", "proto")
    action = _first_value(parsed, "action", "result", "outcome", "decision")
    event_type = (
        _first_value(parsed, "event_type", "category", "channel")
        or payload.source_type
        or parser_name
    )

    return Event(
        timestamp=normalize_timestamp(
            _first_value(parsed, "timestamp", "ts", "event_time"),
            fallback=payload.received_at or utc_now(),
        ),
        source_ip=source_ip,
        dest_ip=dest_ip,
        source_port=source_port,
        dest_port=dest_port,
        protocol=str(protocol).lower() if protocol else None,
        action=str(action).lower() if action else None,
        severity=_normalize_severity(_first_value(parsed, "severity", "level", "priority")),
        event_type=str(event_type).lower().replace(" ", "_"),
        source_system=str(source_system or "unknown"),
        raw_log=payload.raw_log,
        parsed_data=parsed,
        hostname=str(hostname) if hostname else None,
        username=str(username) if username else None,
        message=str(message) if message else payload.raw_log[:500],
        is_demo=payload.is_demo,
    )
