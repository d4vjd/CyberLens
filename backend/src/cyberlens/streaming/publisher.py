# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

import json
from typing import Any, cast

from redis.asyncio import Redis

from cyberlens.detection.models import Alert
from cyberlens.ingestion.models import Event
from cyberlens.streaming.redis_client import get_alert_stream_name, get_event_stream_name


def _serialize_event(event: Event) -> dict[str, str]:
    return {
        "id": str(event.id),
        "timestamp": event.timestamp.isoformat(),
        "event_type": event.event_type,
        "source_system": event.source_system,
        "severity": event.severity.value,
        "source_ip": event.source_ip or "",
        "dest_ip": event.dest_ip or "",
        "action": event.action or "",
        "raw_log": event.raw_log,
        "parsed_data": json.dumps(event.parsed_data),
    }


def _serialize_alert(alert: Alert) -> dict[str, str]:
    return {
        "id": str(alert.id),
        "alert_uid": alert.alert_uid,
        "title": alert.title,
        "severity": alert.severity.value,
        "status": alert.status.value,
        "source_ip": alert.source_ip or "",
        "mitre_tactic": alert.mitre_tactic or "",
        "mitre_technique_id": alert.mitre_technique_id or "",
        "matched_events": json.dumps(alert.matched_events),
        "created_at": alert.created_at.isoformat() if alert.created_at else "",
    }


async def publish_event(redis: Redis, payload: dict[str, Any]) -> str:
    serialized = {key: str(value) for key, value in payload.items()}
    return cast(str, await redis.xadd(get_event_stream_name(), serialized))  # type: ignore[arg-type]


async def publish_events(redis: Redis, events: list[Event]) -> None:
    for event in events:
        await publish_event(redis, _serialize_event(event))


async def publish_alert(redis: Redis, alert: Alert) -> str:
    return cast(str, await redis.xadd(get_alert_stream_name(), _serialize_alert(alert)))  # type: ignore[arg-type]
