# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

import re

from cyberlens.ingestion.parsers.base import BaseParser

KV_RE = re.compile(r"(?P<key>[A-Za-z0-9_.-]+)=(?P<value>\"[^\"]+\"|\S+)")


class FirewallParser(BaseParser):
    parser_name = "firewall"

    def can_parse(self, raw_log: str, source_type: str | None = None) -> bool:
        lowered = raw_log.lower()
        return (
            source_type == "firewall"
            or " src=" in lowered
            or " dst=" in lowered
            or "firewall" in lowered
        )

    def parse(self, raw_log: str) -> dict[str, object]:
        parsed = {
            match.group("key").lower(): match.group("value").strip('"')
            for match in KV_RE.finditer(raw_log)
        }
        action = parsed.get("action") or ("denied" if "deny" in raw_log.lower() else "allowed")
        return {
            "timestamp": parsed.get("timestamp"),
            "event_type": "firewall",
            "source_system": parsed.get("device") or "firewall",
            "severity": "medium" if action == "allowed" else "high",
            "source_ip": parsed.get("src"),
            "dest_ip": parsed.get("dst"),
            "source_port": parsed.get("spt"),
            "dest_port": parsed.get("dpt"),
            "protocol": parsed.get("proto"),
            "action": action,
            "message": raw_log,
        }
