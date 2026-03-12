# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from cyberlens.ingestion.models import Event
from cyberlens.ingestion.normalizer import normalize_event
from cyberlens.ingestion.parsers import ParserRegistry, get_default_parser_registry
from cyberlens.ingestion.schemas import IngestSingleRequest


class LogIngestionPipeline:
    def __init__(self, registry: ParserRegistry | None = None) -> None:
        self.registry = registry or get_default_parser_registry()

    def process(self, payload: IngestSingleRequest) -> tuple[Event, str]:
        parser = self.registry.detect(payload.raw_log, payload.source_type)
        parsed = parser.parse(payload.raw_log)
        event = normalize_event(payload=payload, parsed=parsed, parser_name=parser.parser_name)
        return event, parser.parser_name
