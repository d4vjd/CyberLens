# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from datetime import datetime, timedelta

from cyberlens.demo.types import DemoEventSpec
from cyberlens.ingestion.models import SeverityLevel

SCENARIO_NAME = "port_scan"


def build_port_scan_scenario(anchor: datetime, intensity: int) -> list[DemoEventSpec]:
    source_ip = "203.0.113.17"
    dest_ip = "10.20.1.44"
    ports = [22, 53, 80, 110, 135, 139, 143, 389, 443, 445, 587, 993, 995, 1433, 1521, 2049, 3306, 3389, 5432, 8080]
    if intensity > 5:
        ports.extend([8443, 9200, 9300, 27017, 5000])
    return [
        DemoEventSpec(
            timestamp=anchor + timedelta(seconds=index * 6),
            event_type="network",
            source_system="netflow",
            raw_log=f"SRC={source_ip} DST={dest_ip} PROTO=TCP SPT={40200 + index} DPT={port} FLAGS=SYN",
            severity=SeverityLevel.MEDIUM,
            source_ip=source_ip,
            dest_ip=dest_ip,
            source_port=40200 + index,
            dest_port=port,
            protocol="tcp",
            action="allowed",
            hostname="web-prod-01",
            message="Internal service discovery sweep detected",
            parsed_data={"scenario": SCENARIO_NAME, "phase": "discovery"},
        )
        for index, port in enumerate(ports)
    ]