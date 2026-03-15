# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

"""Baseline telemetry emitter for live mode.

Feeds low-volume operational telemetry into the normal ingestion pipeline so
the live console stays active before external log sources are connected.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from collections import Counter
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from cyberlens.common.time_utils import utc_now
from cyberlens.ingestion.schemas import BaselineEmitterStatus, IngestSingleRequest
from cyberlens.ingestion.service import IngestionService

logger = logging.getLogger(__name__)

_BASELINE_LANES = ("service_health", "service_heartbeat", "network_flow")


@dataclass(frozen=True, slots=True)
class ServiceHeartbeatSpec:
    hostname: str
    source_system: str
    component: str


@dataclass(frozen=True, slots=True)
class NetworkFlowSpec:
    source_label: str
    source_ip: str
    dest_label: str
    dest_ip: str
    dest_port: int
    protocol: str


@dataclass(frozen=True, slots=True)
class HealthCheckResult:
    name: str
    status: str
    latency_ms: float


@dataclass(frozen=True, slots=True)
class BaselineEnvelope:
    lane: str
    payload: IngestSingleRequest


class SupportsIngestBatch(Protocol):
    async def ingest_batch(
        self,
        payloads: list[IngestSingleRequest],
    ): ...


ServiceFactory = Callable[[AsyncSession, Redis], SupportsIngestBatch]

_HEARTBEAT_SERVICES = (
    ServiceHeartbeatSpec(
        hostname="edge-gateway-01",
        source_system="edge-gateway",
        component="north-south-ingress",
    ),
    ServiceHeartbeatSpec(
        hostname="frontend-console-01",
        source_system="frontend-console",
        component="analyst-workspace",
    ),
    ServiceHeartbeatSpec(
        hostname="backend-api-01",
        source_system="backend-api",
        component="ingestion-api",
    ),
    ServiceHeartbeatSpec(
        hostname="detection-engine-01",
        source_system="detection-engine",
        component="rule-evaluator",
    ),
    ServiceHeartbeatSpec(
        hostname="alert-bridge-01",
        source_system="alert-bridge",
        component="websocket-bridge",
    ),
)

_NETWORK_FLOWS = (
    NetworkFlowSpec(
        source_label="edge-gateway",
        source_ip="10.20.0.10",
        dest_label="frontend-console",
        dest_ip="10.20.0.20",
        dest_port=5173,
        protocol="TCP",
    ),
    NetworkFlowSpec(
        source_label="frontend-console",
        source_ip="10.20.0.20",
        dest_label="backend-api",
        dest_ip="10.20.0.30",
        dest_port=8000,
        protocol="TCP",
    ),
    NetworkFlowSpec(
        source_label="backend-api",
        source_ip="10.20.0.30",
        dest_label="mysql-primary",
        dest_ip="10.20.0.40",
        dest_port=3306,
        protocol="TCP",
    ),
    NetworkFlowSpec(
        source_label="backend-api",
        source_ip="10.20.0.30",
        dest_label="redis-streams",
        dest_ip="10.20.0.50",
        dest_port=6379,
        protocol="TCP",
    ),
    NetworkFlowSpec(
        source_label="detection-engine",
        source_ip="10.20.0.60",
        dest_label="redis-streams",
        dest_ip="10.20.0.50",
        dest_port=6379,
        protocol="TCP",
    ),
    NetworkFlowSpec(
        source_label="alert-bridge",
        source_ip="10.20.0.70",
        dest_label="redis-streams",
        dest_ip="10.20.0.50",
        dest_port=6379,
        protocol="TCP",
    ),
)


def _default_ingestion_service(session: AsyncSession, redis: Redis) -> IngestionService:
    return IngestionService(session=session, redis=redis)


def build_default_baseline_status() -> BaselineEmitterStatus:
    return BaselineEmitterStatus(
        running=False,
        event_mix={lane: 0 for lane in _BASELINE_LANES},
        parser_mix={},
        last_checks={},
        monitored_services=[service.source_system for service in _HEARTBEAT_SERVICES],
    )


class BaselineEmitter:
    """Emit benign operational telemetry through the live ingestion pipeline."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        redis: Redis,
        *,
        service_factory: ServiceFactory | None = None,
        min_delay_seconds: float = 4.0,
        max_delay_seconds: float = 8.0,
        random_seed: int | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._redis = redis
        self._service_factory = service_factory or _default_ingestion_service
        self._min_delay_seconds = min_delay_seconds
        self._max_delay_seconds = max_delay_seconds
        self._task: asyncio.Task[None] | None = None
        self._running = False
        self._rng = random.Random(random_seed)  # nosec B311
        self._status = build_default_baseline_status()

    def status(self) -> BaselineEmitterStatus:
        return self._status.model_copy(deep=True)

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._status.running = True
        self._task = asyncio.create_task(self._run(), name="cyberlens-baseline-emitter")

    async def stop(self) -> None:
        self._running = False
        self._status.running = False
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def aclose(self) -> None:
        await self.stop()

    async def _run(self) -> None:
        while self._running:
            try:
                await self._emit_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self._status.last_error = str(exc)
                logger.warning("Baseline telemetry emitter iteration failed: %s", exc)

            await asyncio.sleep(self._rng.uniform(self._min_delay_seconds, self._max_delay_seconds))

    async def _emit_once(self) -> None:
        emitted_at = utc_now()

        async with self._session_factory() as session:
            health_checks = await self._collect_stack_health(session)
            envelopes = self._build_batch(emitted_at, health_checks)
            service = self._service_factory(session, self._redis)
            response = await service.ingest_batch([envelope.payload for envelope in envelopes])

        batch_mix = Counter(envelope.lane for envelope in envelopes)
        parser_mix = Counter(response.parser_counts)
        self._status.running = self._running
        self._status.emitted_batches += 1
        self._status.emitted_events += response.ingested_count
        self._status.last_batch_size = response.ingested_count
        self._status.last_emit_at = emitted_at
        self._status.last_ingested_at = max(
            (event.timestamp for event in response.events),
            default=emitted_at,
        )
        self._status.last_checks = {
            check.name: f"{check.status} ({check.latency_ms:.1f} ms)" for check in health_checks
        }
        self._status.last_error = None

        for lane, count in batch_mix.items():
            self._status.event_mix[lane] = self._status.event_mix.get(lane, 0) + count
        for parser_name, count in parser_mix.items():
            self._status.parser_mix[parser_name] = (
                self._status.parser_mix.get(parser_name, 0) + count
            )

    async def _collect_stack_health(self, session: AsyncSession) -> list[HealthCheckResult]:
        db_started = time.perf_counter()
        await session.execute(text("SELECT 1"))
        db_latency_ms = (time.perf_counter() - db_started) * 1000

        redis_started = time.perf_counter()
        await self._redis.ping()
        redis_latency_ms = (time.perf_counter() - redis_started) * 1000

        return [
            HealthCheckResult(name="mysql", status="ok", latency_ms=db_latency_ms),
            HealthCheckResult(name="redis", status="ok", latency_ms=redis_latency_ms),
        ]

    def _build_batch(
        self,
        emitted_at: datetime,
        health_checks: list[HealthCheckResult],
    ) -> list[BaselineEnvelope]:
        flow_count = self._rng.randint(2, 3)
        heartbeat_count = self._rng.randint(2, 3)
        batch: list[BaselineEnvelope] = [
            self._build_health_probe(emitted_at, health_checks),
        ]
        batch.extend(
            self._build_service_heartbeat(emitted_at, spec)
            for spec in self._pick_services(heartbeat_count)
        )
        batch.extend(
            self._build_network_flow(emitted_at, flow) for flow in self._pick_flows(flow_count)
        )
        return batch

    def _build_health_probe(
        self,
        emitted_at: datetime,
        health_checks: list[HealthCheckResult],
    ) -> BaselineEnvelope:
        degraded = any(check.status != "ok" for check in health_checks)
        checks_payload = {
            check.name: {
                "status": check.status,
                "latency_ms": round(check.latency_ms, 2),
            }
            for check in health_checks
        }
        message = "Control plane health probe mysql={mysql} redis={redis}".format(
            mysql=checks_payload["mysql"]["status"],
            redis=checks_payload["redis"]["status"],
        )
        payload = IngestSingleRequest(
            raw_log=(
                "{"
                f'"timestamp":"{emitted_at.isoformat()}",'
                '"event_type":"service_health",'
                '"source_system":"platform-probe",'
                '"hostname":"platform-probe-01",'
                f'"severity":"{"high" if degraded else "low"}",'
                f'"action":"{"degraded" if degraded else "healthy"}",'
                f'"message":"{message}",'
                f'"checks":{self._json_checks(checks_payload)}'
                "}"
            ),
            source_type="json",
            is_demo=False,
            received_at=emitted_at,
        )
        return BaselineEnvelope(lane="service_health", payload=payload)

    def _build_service_heartbeat(
        self,
        emitted_at: datetime,
        spec: ServiceHeartbeatSpec,
    ) -> BaselineEnvelope:
        payload = IngestSingleRequest(
            raw_log=(
                f"<14>1 {self._isoformat_z(emitted_at)} {spec.hostname} {spec.source_system} 4200 "
                "BEAT - "
                "event_type=service_heartbeat "
                "severity=low "
                "action=alive "
                f'component="{spec.component}" '
                'message="Routine service heartbeat acknowledged by the platform monitor"'
            ),
            source_type="syslog",
            is_demo=False,
            received_at=emitted_at,
        )
        return BaselineEnvelope(lane="service_heartbeat", payload=payload)

    def _build_network_flow(
        self,
        emitted_at: datetime,
        spec: NetworkFlowSpec,
    ) -> BaselineEnvelope:
        source_port = self._rng.randint(32768, 60999)
        bytes_transferred = self._rng.randint(8_192, 262_144)
        payload = IngestSingleRequest(
            raw_log=(
                f"timestamp={self._isoformat_z(emitted_at)} "
                "exporter=mesh-observer-01 "
                "event_type=network_flow "
                "severity=low "
                f"src_ip={spec.source_ip} "
                f"dst_ip={spec.dest_ip} "
                f"src_port={source_port} "
                f"dst_port={spec.dest_port} "
                f"protocol={spec.protocol} "
                f"bytes={bytes_transferred} "
                f'message="Routine service path {spec.source_label} -> {spec.dest_label}"'
            ),
            source_type="netflow",
            is_demo=False,
            received_at=emitted_at,
        )
        return BaselineEnvelope(lane="network_flow", payload=payload)

    def _pick_services(self, count: int) -> list[ServiceHeartbeatSpec]:
        return self._rng.sample(list(_HEARTBEAT_SERVICES), k=min(count, len(_HEARTBEAT_SERVICES)))

    def _pick_flows(self, count: int) -> list[NetworkFlowSpec]:
        return self._rng.sample(list(_NETWORK_FLOWS), k=min(count, len(_NETWORK_FLOWS)))

    def _isoformat_z(self, value: datetime) -> str:
        return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _json_checks(self, payload: dict[str, dict[str, object]]) -> str:
        items = []
        for key, value in payload.items():
            items.append(
                f'"{key}":{{"status":"{value["status"]}",'
                f'"latency_ms":{float(value["latency_ms"]):.2f}}}'
            )
        return "{" + ",".join(items) + "}"
