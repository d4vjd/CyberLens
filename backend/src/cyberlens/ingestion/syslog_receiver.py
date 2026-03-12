# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from cyberlens.config import Settings
from cyberlens.db.session import SessionLocal
from cyberlens.ingestion.schemas import IngestSingleRequest
from cyberlens.ingestion.service import IngestionService
from cyberlens.streaming.redis_client import build_redis_client


class _SyslogDatagramProtocol(asyncio.DatagramProtocol):
    def __init__(self, handler: Callable[[str, tuple[Any, ...] | None], Awaitable[None]]) -> None:
        self.handler = handler

    def datagram_received(self, data: bytes, addr: tuple[Any, ...]) -> None:
        asyncio.create_task(self.handler(data.decode("utf-8", errors="replace"), addr))  # type: ignore[arg-type]


class SyslogReceiver:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._udp_transport: asyncio.DatagramTransport | None = None
        self._tcp_server: asyncio.AbstractServer | None = None

    async def start(self) -> None:
        if not self.settings.syslog_enabled:
            return

        loop = asyncio.get_running_loop()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: _SyslogDatagramProtocol(self._ingest_message),
            local_addr=(self.settings.syslog_bind_host, self.settings.syslog_bind_port),
        )
        self._udp_transport = transport
        self._tcp_server = await asyncio.start_server(
            self._handle_tcp_client,
            host=self.settings.syslog_bind_host,
            port=self.settings.syslog_bind_port,
        )

    async def stop(self) -> None:
        if self._udp_transport is not None:
            self._udp_transport.close()
            self._udp_transport = None
        if self._tcp_server is not None:
            self._tcp_server.close()
            await self._tcp_server.wait_closed()
            self._tcp_server = None

    async def _handle_tcp_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        peername = writer.get_extra_info("peername")
        try:
            while data := await reader.readline():
                await self._ingest_message(data.decode("utf-8", errors="replace"), peername)
        finally:
            writer.close()
            await writer.wait_closed()

    async def _ingest_message(self, raw_log: str, peername: tuple[Any, ...] | None) -> None:
        if not raw_log.strip():
            return

        redis = build_redis_client()
        try:
            async with SessionLocal() as session:
                service = IngestionService(session=session, redis=redis)
                source_system = "syslog"
                if peername and len(peername) > 0:
                    source_system = f"syslog:{peername[0]}"
                await service.ingest_batch(
                    [
                        IngestSingleRequest(
                            raw_log=raw_log.strip(),
                            source_system=source_system,
                            source_type="syslog",
                        )
                    ]
                )
        finally:
            await redis.aclose()
