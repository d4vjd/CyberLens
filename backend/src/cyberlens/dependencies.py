# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from collections.abc import AsyncIterator

from redis.asyncio import Redis

from cyberlens.config import Settings, get_settings
from cyberlens.db.session import get_db_session


async def get_settings_dependency() -> Settings:
    return get_settings()


async def get_redis_client() -> AsyncIterator[Redis]:
    settings = get_settings()
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


__all__ = ["get_db_session", "get_redis_client", "get_settings_dependency"]
