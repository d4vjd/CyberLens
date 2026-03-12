# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from cyberlens.config import get_settings
from cyberlens.detection.service import DetectionService
from cyberlens.streaming.consumer import ack_stream_message, ensure_consumer_group, read_stream_group
from cyberlens.streaming.redis_client import get_alert_stream_name, get_event_stream_name

logger = logging.getLogger(__name__)


class DetectionEngine:
    def __init__(
        self,
        session_factory: async_sessionmaker,
        redis: Redis,
    ) -> None:
        settings = get_settings()
        self.session_factory = session_factory
        self.redis = redis
        self.consumer_group = settings.detection_consumer_group
        self.consumer_name = settings.detection_consumer_name
        self.poll_ms = settings.detection_poll_ms
        self._task: asyncio.Task[None] | None = None
        self._running = False

    async def start(self) -> None:
        await ensure_consumer_group(
            self.redis,
            stream_name=get_event_stream_name(),
            group_name=self.consumer_group,
        )
        await ensure_consumer_group(
            self.redis,
            stream_name=get_alert_stream_name(),
            group_name=get_settings().websocket_consumer_group,
        )
        self._running = True
        self._task = asyncio.create_task(self._run(), name="cyberlens-detection-engine")

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _run(self) -> None:
        while self._running:
            try:
                messages = await read_stream_group(
                    self.redis,
                    stream_name=get_event_stream_name(),
                    group_name=self.consumer_group,
                    consumer_name=self.consumer_name,
                    count=50,
                    block=self.poll_ms,
                )
                if not messages:
                    continue

                async with self.session_factory() as session:
                    service = DetectionService(session=session, redis=self.redis)
                    for _, entries in messages:
                        for message_id, payload in entries:
                            await service.process_stream_event(payload)
                            await ack_stream_message(
                                self.redis,
                                stream_name=get_event_stream_name(),
                                group_name=self.consumer_group,
                                message_id=message_id,
                            )
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Detection engine iteration failed")
                await asyncio.sleep(1)