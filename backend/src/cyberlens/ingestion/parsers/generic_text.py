# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from cyberlens.ingestion.parsers.base import BaseParser


class GenericTextParser(BaseParser):
    parser_name = "generic_text"

    def can_parse(self, raw_log: str, source_type: str | None = None) -> bool:
        return True

    def parse(self, raw_log: str) -> dict[str, object]:
        return {
            "event_type": "generic",
            "source_system": "generic",
            "severity": "medium",
            "message": raw_log,
        }