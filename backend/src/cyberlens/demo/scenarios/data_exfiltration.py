# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from datetime import datetime, timedelta

from cyberlens.demo.types import DemoEventSpec
from cyberlens.ingestion.models import SeverityLevel

SCENARIO_NAME = "data_exfiltration"


def build_data_exfiltration_scenario(anchor: datetime, intensity: int) -> list[DemoEventSpec]:
    source_ip = "10.20.5.14"
    hostname = "linux-batch-03"
    queries = max(2, intensity)
    return [
        DemoEventSpec(
            timestamp=anchor + timedelta(seconds=index * 21),
            event_type="dns",
            source_system="firewall",
            raw_log=(
                f'{{"src_ip":"{source_ip}","dest_ip":"203.0.113.91","query":"bulk-{index}.demo.local","type":"TXT"}}'
            ),
            severity=SeverityLevel.CRITICAL,
            source_ip=source_ip,
            dest_ip="203.0.113.91",
            source_port=54000 + index,
            dest_port=53,
            protocol="udp",
            action="allowed",
            hostname=hostname,
            username="svc-backup",
            message="Suspicious high-entropy TXT lookup during staged exfiltration",
            parsed_data={"scenario": SCENARIO_NAME, "phase": "exfiltration", "record_type": "TXT"},
        )
        for index in range(queries)
    ]
