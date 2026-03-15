# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

import re
from datetime import UTC, datetime

from cyberlens.ingestion.parsers.base import BaseParser

RFC3164_RE = re.compile(
    r"^<(?P<priority>\d+)>(?P<timestamp>[A-Z][a-z]{2}\s+\d{1,2}\s\d{2}:\d{2}:\d{2}) "
    r"(?P<hostname>\S+) (?P<tag>[\w\-/\.]+)(?:\[(?P<pid>\d+)\])?: (?P<message>.*)$"
)
RFC5424_RE = re.compile(
    r"^<(?P<priority>\d+)>(?P<version>\d+) (?P<timestamp>\S+) "
    r"(?P<hostname>\S+) (?P<appname>\S+) (?P<procid>\S+) "
    r"(?P<msgid>\S+) (?P<structured_data>(?:-|\[.*?\])) "
    r"(?P<message>.*)$"
)
KV_RE = re.compile(r"(?P<key>[A-Za-z0-9_.-]+)=(?P<value>\"[^\"]+\"|\S+)")
SSH_FAILED_RE = re.compile(
    r"Failed password for (?:invalid user )?(?P<username>\S+) "
    r"from (?P<source_ip>\S+) port (?P<port>\d+)"
)


def _extract_key_values(message: str) -> dict[str, object]:
    parsed: dict[str, object] = {}
    for match in KV_RE.finditer(message):
        parsed[match.group("key").lower()] = match.group("value").strip('"')
    return parsed


class SyslogParser(BaseParser):
    parser_name = "syslog"

    def can_parse(self, raw_log: str, source_type: str | None = None) -> bool:
        return source_type == "syslog" or raw_log.startswith("<")

    def parse(self, raw_log: str) -> dict[str, object]:
        if match := RFC5424_RE.match(raw_log):
            payload = match.groupdict()
            message = str(payload["message"])
            parsed = _extract_key_values(message)
            parsed.update(self._extract_auth_fields(message))
            parsed.update(
                {
                    "timestamp": payload["timestamp"],
                    "hostname": payload["hostname"],
                    "source_system": payload["appname"],
                    "message": message,
                    "priority": int(payload["priority"]),
                    "event_type": parsed.get("event_type")
                    or self._infer_event_type(message, payload["appname"]),
                    "severity": self._severity_from_priority(int(payload["priority"])),
                }
            )
            return parsed

        if match := RFC3164_RE.match(raw_log):
            payload = match.groupdict()
            current_year = datetime.now(tz=UTC).year
            timestamp = datetime.strptime(
                f"{current_year} {payload['timestamp']}",
                "%Y %b %d %H:%M:%S",
            ).replace(tzinfo=UTC)
            message = str(payload["message"])
            parsed = _extract_key_values(message)
            parsed.update(self._extract_auth_fields(message))
            parsed.update(
                {
                    "timestamp": timestamp.isoformat(),
                    "hostname": payload["hostname"],
                    "source_system": payload["tag"],
                    "message": message,
                    "priority": int(payload["priority"]),
                    "event_type": parsed.get("event_type")
                    or self._infer_event_type(message, payload["tag"]),
                    "severity": self._severity_from_priority(int(payload["priority"])),
                }
            )
            return parsed

        return {
            "message": raw_log,
            "event_type": "syslog",
            "source_system": "syslog",
            "severity": "medium",
        }

    def _severity_from_priority(self, priority: int) -> str:
        severity = priority % 8
        if severity <= 2:
            return "critical"
        if severity <= 4:
            return "high"
        if severity == 5:
            return "medium"
        return "low"

    def _infer_event_type(self, message: str, source_system: str) -> str:
        lowered = f"{source_system} {message}".lower()
        if "failed password" in lowered or "authentication failure" in lowered:
            return "authentication"
        if "deny" in lowered or "blocked" in lowered:
            return "firewall"
        if "flow" in lowered:
            return "network"
        return "syslog"

    def _extract_auth_fields(self, message: str) -> dict[str, object]:
        match = SSH_FAILED_RE.search(message)
        if not match:
            return {}
        return {
            "username": match.group("username"),
            "source_ip": match.group("source_ip"),
            "dest_port": 22,
            "action": "failed",
        }
