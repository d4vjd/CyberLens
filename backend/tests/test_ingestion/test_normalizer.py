# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from datetime import UTC, datetime

from cyberlens.ingestion.normalizer import normalize_event
from cyberlens.ingestion.schemas import IngestSingleRequest


def test_normalize_event_preserves_low_severity() -> None:
    event = normalize_event(
        IngestSingleRequest(
            raw_log="severity=low event_type=network_flow",
            source_type="netflow",
            received_at=datetime(2026, 3, 14, 12, 30, tzinfo=UTC),
        ),
        parsed={
            "timestamp": "2026-03-14T12:30:00Z",
            "event_type": "network_flow",
            "source_system": "mesh-observer-01",
            "severity": "low",
            "message": "Routine path observed",
        },
        parser_name="netflow",
    )

    assert event.severity.value == "low"
