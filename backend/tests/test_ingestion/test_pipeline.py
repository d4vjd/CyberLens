# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from cyberlens.ingestion.pipeline import LogIngestionPipeline
from cyberlens.ingestion.schemas import IngestSingleRequest


def test_syslog_pipeline_normalizes_authentication_event() -> None:
    pipeline = LogIngestionPipeline()
    payload = IngestSingleRequest(
        raw_log=(
            "<34>1 2026-03-12T16:12:04Z web-prod-01 sshd 1234 ID47 - "
            "Failed password for invalid user admin from 198.51.100.24 port 22"
        ),
        source_type="syslog",
    )

    event, parser_name = pipeline.process(payload)

    assert parser_name == "syslog"
    assert event.event_type == "authentication"
    assert event.hostname == "web-prod-01"
    assert event.source_system == "sshd"
    assert event.source_ip == "198.51.100.24"
    assert event.dest_port == 22
    assert event.action == "failed"
    assert event.severity.value in {"high", "critical"}


def test_json_pipeline_preserves_network_fields() -> None:
    pipeline = LogIngestionPipeline()
    payload = IngestSingleRequest(
        raw_log=(
            '{"timestamp":"2026-03-12T16:12:10Z","event_type":"network",'
            '"source_system":"sensor-a","source_ip":"10.0.0.8","dest_ip":"10.0.0.9",'
            '"dest_port":443,"protocol":"TCP","message":"TLS handshake"}'
        ),
        source_type="json",
    )

    event, parser_name = pipeline.process(payload)

    assert parser_name == "json_generic"
    assert event.event_type == "network"
    assert event.source_ip == "10.0.0.8"
    assert event.dest_ip == "10.0.0.9"
    assert event.dest_port == 443
    assert event.protocol == "tcp"