# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

import json

from cyberlens.ingestion.parsers.base import BaseParser


class JsonGenericParser(BaseParser):
    parser_name = "json_generic"

    def can_parse(self, raw_log: str, source_type: str | None = None) -> bool:
        if source_type == "json":
            return True
        try:
            json.loads(raw_log)
        except json.JSONDecodeError:
            return False
        return True

    def parse(self, raw_log: str) -> dict[str, object]:
        parsed = json.loads(raw_log)
        if isinstance(parsed, dict):
            return parsed
        return {
            "event_type": "json_generic",
            "source_system": "json",
            "message": json.dumps(parsed),
        }
