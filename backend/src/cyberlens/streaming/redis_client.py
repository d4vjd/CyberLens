# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from typing import cast

from redis.asyncio import Redis

from cyberlens.config import get_settings


def build_redis_client() -> Redis:
    settings = get_settings()
    return cast(Redis, Redis.from_url(settings.redis_url, decode_responses=True))


def get_event_stream_name() -> str:
    return get_settings().redis_event_stream


def get_alert_stream_name() -> str:
    return get_settings().redis_alert_stream
