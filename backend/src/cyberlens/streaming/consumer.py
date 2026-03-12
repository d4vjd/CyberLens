# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from typing import Any

from redis.asyncio import Redis
from redis.exceptions import ResponseError


async def ensure_consumer_group(redis: Redis, stream_name: str, group_name: str) -> None:
    try:
        await redis.xgroup_create(stream_name, group_name, id="0", mkstream=True)
    except ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise


async def read_stream_group(
    redis: Redis,
    stream_name: str,
    group_name: str,
    consumer_name: str,
    count: int = 100,
    block: int | None = None,
) -> list[tuple[str, list[tuple[str, dict[str, Any]]]]]:
    return await redis.xreadgroup(
        groupname=group_name,
        consumername=consumer_name,
        streams={stream_name: ">"},
        count=count,
        block=block,
    )


async def ack_stream_message(
    redis: Redis,
    stream_name: str,
    group_name: str,
    message_id: str,
) -> None:
    await redis.xack(stream_name, group_name, message_id)