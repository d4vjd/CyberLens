# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

import re

from cyberlens.ingestion.parsers.base import BaseParser

KV_RE = re.compile(r"(?P<key>[A-Za-z0-9_.-]+)=(?P<value>\"[^\"]+\"|\S+)")


class NetflowParser(BaseParser):
    parser_name = "netflow"

    def can_parse(self, raw_log: str, source_type: str | None = None) -> bool:
        lowered = raw_log.lower()
        return source_type == "netflow" or (
            "src_ip" in lowered and "dst_ip" in lowered and "bytes" in lowered
        )

    def parse(self, raw_log: str) -> dict[str, object]:
        parsed = {
            match.group("key").lower(): match.group("value").strip('"')
            for match in KV_RE.finditer(raw_log)
        }
        return {
            "timestamp": parsed.get("timestamp"),
            "event_type": "network",
            "source_system": parsed.get("exporter") or "netflow",
            "severity": "low",
            "source_ip": parsed.get("src_ip"),
            "dest_ip": parsed.get("dst_ip"),
            "source_port": parsed.get("src_port"),
            "dest_port": parsed.get("dst_port"),
            "protocol": parsed.get("protocol"),
            "message": raw_log,
            "bytes": parsed.get("bytes"),
        }
