# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from datetime import datetime

from cyberlens.demo.types import DemoEventSpec
from cyberlens.ingestion.models import SeverityLevel

SCENARIO_NAME = "privilege_escalation"


def build_privilege_escalation_scenario(anchor: datetime, intensity: int) -> list[DemoEventSpec]:
    del intensity
    return [
        DemoEventSpec(
            timestamp=anchor,
            event_type="process",
            source_system="linux",
            raw_log="sudo: svc-backup : TTY=pts/2 ; PWD=/tmp ; USER=root ; COMMAND=/bin/bash",
            severity=SeverityLevel.CRITICAL,
            source_ip="10.20.5.14",
            protocol=None,
            action="executed",
            hostname="linux-batch-03",
            username="svc-backup",
            message="svc-backup invoked sudo to spawn an interactive shell",
            parsed_data={"scenario": SCENARIO_NAME, "phase": "privilege-escalation"},
        )
    ]