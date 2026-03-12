# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

import json

from cyberlens.ingestion.parsers.base import BaseParser


class WindowsEventParser(BaseParser):
    parser_name = "windows_event"

    def can_parse(self, raw_log: str, source_type: str | None = None) -> bool:
        if source_type == "windows_event":
            return True
        if "EventID" in raw_log or "WinEventLog" in raw_log:
            return True
        try:
            parsed = json.loads(raw_log)
        except json.JSONDecodeError:
            return False
        return "EventID" in parsed or "event_id" in parsed or parsed.get("channel") == "Security"

    def parse(self, raw_log: str) -> dict[str, object]:
        try:
            parsed = json.loads(raw_log)
        except json.JSONDecodeError:
            parts = dict(segment.split("=", 1) for segment in raw_log.split() if "=" in segment)
            event_id = parts.get("EventID") or parts.get("event_id")
            return {
                "event_type": "authentication" if str(event_id) == "4625" else "windows_event",
                "source_system": "windows",
                "severity": "medium",
                "message": raw_log,
                "username": parts.get("TargetUserName"),
                "hostname": parts.get("Computer"),
            }

        event_id = parsed.get("EventID") or parsed.get("event_id")
        return {
            "timestamp": parsed.get("TimeCreated") or parsed.get("timestamp"),
            "event_type": "authentication"
            if str(event_id) in {"4624", "4625"}
            else "windows_event",
            "source_system": "windows",
            "severity": parsed.get("level", "medium"),
            "message": parsed.get("Message") or parsed.get("message") or raw_log,
            "username": parsed.get("TargetUserName") or parsed.get("username"),
            "hostname": parsed.get("Computer") or parsed.get("hostname"),
            "source_ip": parsed.get("IpAddress") or parsed.get("source_ip"),
            "action": "failed"
            if str(event_id) == "4625"
            else "success"
            if str(event_id) == "4624"
            else None,
        }
