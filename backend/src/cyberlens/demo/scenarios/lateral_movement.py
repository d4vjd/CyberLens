# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from datetime import datetime, timedelta

from cyberlens.demo.types import DemoEventSpec
from cyberlens.ingestion.models import SeverityLevel

SCENARIO_NAME = "lateral_movement"


def build_lateral_movement_scenario(anchor: datetime, intensity: int) -> list[DemoEventSpec]:
    source_ip = "10.20.4.88"
    hosts = ("10.20.5.14", "10.20.5.21", "10.20.5.32")
    attempts = max(10, 10 + intensity)
    return [
        DemoEventSpec(
            timestamp=anchor + timedelta(seconds=index * 12),
            event_type="network",
            source_system="windows",
            raw_log=(
                f"SRC={source_ip} DST={hosts[index % len(hosts)]} PROTO=TCP "
                f"SPT={40000 + index} DPT=445 ACTION=allowed"
            ),
            severity=SeverityLevel.HIGH,
            source_ip=source_ip,
            dest_ip=hosts[index % len(hosts)],
            source_port=40000 + index,
            dest_port=445,
            protocol="tcp",
            action="allowed",
            hostname="wks-finance-14",
            username="svc-backup",
            message="Repeated SMB connection attempts across peer systems",
            parsed_data={"scenario": SCENARIO_NAME, "phase": "lateral-movement"},
        )
        for index in range(attempts)
    ]
