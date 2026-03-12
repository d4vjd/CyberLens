# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from datetime import datetime, timedelta

from cyberlens.demo.types import DemoEventSpec
from cyberlens.ingestion.models import SeverityLevel

SCENARIO_NAME = "brute_force"


def build_brute_force_scenario(anchor: datetime, intensity: int) -> list[DemoEventSpec]:
    source_ip = "198.51.100.42"
    hostname = "bastion-edge-01"
    attempts = max(5, 5 + intensity // 2)
    return [
        DemoEventSpec(
            timestamp=anchor + timedelta(seconds=index * 18),
            event_type="authentication",
            source_system="sshd",
            raw_log=(
                f"<34>Mar 12 09:10:{index:02d} {hostname} sshd[22{index:02d}]: "
                f"Failed password for invalid user admin from {source_ip} port {51100 + index} ssh2"
            ),
            severity=SeverityLevel.HIGH if index < attempts - 1 else SeverityLevel.CRITICAL,
            source_ip=source_ip,
            dest_ip="10.20.3.12",
            source_port=51100 + index,
            dest_port=22,
            protocol="tcp",
            action="failed",
            hostname=hostname,
            username="admin",
            message=f"Failed password for invalid user admin from {source_ip}",
            parsed_data={"scenario": SCENARIO_NAME, "phase": "credential-access"},
        )
        for index in range(attempts)
    ]