# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from cyberlens.ingestion.baseline_emitter import BaselineEmitter
from cyberlens.ingestion.schemas import IngestedEventSummary, IngestResponse, IngestSingleRequest


class DummyRedis:
    async def ping(self) -> bool:
        return True


class DummySession:
    async def execute(self, _: object) -> None:
        return None


class DummySessionContext:
    def __init__(self, session: DummySession) -> None:
        self._session = session

    async def __aenter__(self) -> DummySession:
        return self._session

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        del exc_type, exc, tb
        return False


class DummySessionFactory:
    def __init__(self, session: DummySession) -> None:
        self._session = session

    def __call__(self) -> DummySessionContext:
        return DummySessionContext(self._session)


class RecordingIngestionService:
    def __init__(self, payloads: list[IngestSingleRequest]) -> None:
        self._payloads = payloads

    async def ingest_batch(self, payloads: list[IngestSingleRequest]) -> IngestResponse:
        self._payloads.extend(payloads)
        now = datetime(2026, 3, 14, 12, 30, tzinfo=UTC)
        return IngestResponse(
            ingested_count=len(payloads),
            parser_counts={"json_generic": 1, "syslog": 2, "netflow": len(payloads) - 3},
            events=[
                IngestedEventSummary(
                    id=index + 1,
                    timestamp=now,
                    event_type="baseline",
                    source_system="baseline-emitter",
                    parser_name="json_generic",
                )
                for index, _ in enumerate(payloads)
            ],
        )


def test_baseline_emitter_uses_live_ingestion_pipeline() -> None:
    async def run_scenario() -> tuple[list[IngestSingleRequest], object]:
        captured: list[IngestSingleRequest] = []
        emitter = BaselineEmitter(
            session_factory=DummySessionFactory(DummySession()),  # type: ignore[arg-type]
            redis=DummyRedis(),  # type: ignore[arg-type]
            service_factory=lambda session, redis: RecordingIngestionService(captured),
            random_seed=7,
        )

        await emitter._emit_once()
        return captured, emitter.status()

    captured, status = asyncio.run(run_scenario())

    assert captured
    assert all(payload.is_demo is False for payload in captured)
    assert {payload.source_type for payload in captured} == {"json", "syslog", "netflow"}
    assert status.pipeline == "live_ingestion"
    assert status.emitted_batches == 1
    assert status.emitted_events == len(captured)
    assert status.event_mix["service_health"] == 1
    assert status.event_mix["service_heartbeat"] >= 2
    assert status.event_mix["network_flow"] >= 2
    assert status.parser_mix["json_generic"] == 1
    assert status.last_checks["mysql"].startswith("ok")
    assert any(
        "severity=low" in payload.raw_log for payload in captured if payload.source_type == "syslog"
    )
    assert any(
        "severity=low" in payload.raw_log
        for payload in captured
        if payload.source_type == "netflow"
    )
