# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import suppress

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from redis.asyncio import Redis

from cyberlens.config import get_settings
from cyberlens.streaming.consumer import ack_stream_message, ensure_consumer_group, read_stream_group
from cyberlens.streaming.redis_client import get_alert_stream_name

router = APIRouter(prefix="/ws", tags=["streaming"])
logger = logging.getLogger(__name__)


class AlertBroadcastHub:
    def __init__(self) -> None:
        self.connections: set[WebSocket] = set()
        self._task: asyncio.Task[None] | None = None
        self._running = False
        self._redis: Redis | None = None

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.connections.discard(websocket)

    async def broadcast(self, payload: dict[str, object]) -> None:
        stale: list[WebSocket] = []
        for websocket in self.connections:
            try:
                await websocket.send_json(payload)
            except RuntimeError:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(websocket)

    async def start(self, redis: Redis) -> None:
        settings = get_settings()
        self._redis = redis
        await ensure_consumer_group(redis, get_alert_stream_name(), settings.websocket_consumer_group)
        self._running = True
        self._task = asyncio.create_task(
            self._run(redis, settings.websocket_consumer_group, settings.websocket_consumer_name),
            name="cyberlens-alert-ws-bridge",
        )

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None

    async def _run(self, redis: Redis, group_name: str, consumer_name: str) -> None:
        while self._running:
            try:
                messages = await read_stream_group(
                    redis,
                    stream_name=get_alert_stream_name(),
                    group_name=group_name,
                    consumer_name=consumer_name,
                    count=20,
                    block=1000,
                )
                if not messages:
                    continue

                for _, entries in messages:
                    for message_id, payload in entries:
                        await self.broadcast(
                            {
                                "type": "alert",
                                "payload": {
                                    **payload,
                                    "matched_events": json.loads(payload.get("matched_events", "[]")),
                                },
                            }
                        )
                        await ack_stream_message(
                            redis,
                            stream_name=get_alert_stream_name(),
                            group_name=group_name,
                            message_id=message_id,
                        )
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Alert websocket bridge iteration failed")
                await asyncio.sleep(1)


alert_hub = AlertBroadcastHub()


@router.websocket("/alerts")
async def alerts_socket(websocket: WebSocket) -> None:
    await alert_hub.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        alert_hub.disconnect(websocket)