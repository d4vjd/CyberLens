# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

import random
from collections.abc import Sequence
from datetime import timedelta

from cyberlens.common.time_utils import utc_now
from cyberlens.demo.scenarios.brute_force import build_brute_force_scenario
from cyberlens.demo.scenarios.data_exfiltration import build_data_exfiltration_scenario
from cyberlens.demo.scenarios.lateral_movement import build_lateral_movement_scenario
from cyberlens.demo.scenarios.port_scan import build_port_scan_scenario
from cyberlens.demo.scenarios.privilege_escalation import build_privilege_escalation_scenario
from cyberlens.demo.types import DemoEventSpec
from cyberlens.ingestion.models import SeverityLevel

BASELINE_HOSTS: Sequence[tuple[str, str]] = (
    ("web-prod-01", "10.20.1.10"),
    ("api-prod-02", "10.20.1.22"),
    ("vpn-edge-01", "10.20.2.5"),
    ("db-prod-01", "10.20.3.11"),
    ("wks-finance-14", "10.20.4.88"),
    ("srv-hr-02", "10.20.5.14"),
)

BASELINE_USERS = ("jmartin", "alee", "snguyen", "svc-backup", "system")
BASELINE_MESSAGES = (
    ("authentication", "vpn", "success", "VPN session established", SeverityLevel.LOW),
    ("dns", "firewall", "allowed", "Standard DNS lookup to approved resolver", SeverityLevel.LOW),
    ("network", "firewall", "allowed", "Routine east-west traffic permitted", SeverityLevel.LOW),
    ("firewall", "firewall", "denied", "Low-volume deny on retired segment", SeverityLevel.MEDIUM),
)


def build_seed_dataset(days: int, intensity: int, event_count: int) -> list[DemoEventSpec]:
    rng = random.Random(20260312 + intensity + days + event_count)  # nosec B311
    now = utc_now()
    start = now - timedelta(days=days)

    attack_events: list[DemoEventSpec] = []
    anchors = [
        start + timedelta(hours=14),
        start + timedelta(days=1, hours=10),
        start + timedelta(days=2, hours=9, minutes=30),
        start + timedelta(days=3, hours=11),
        start + timedelta(days=4, hours=12, minutes=15),
    ]
    attack_events.extend(build_port_scan_scenario(anchors[0], intensity))
    attack_events.extend(build_brute_force_scenario(anchors[1], intensity))
    attack_events.extend(build_lateral_movement_scenario(anchors[2], intensity))
    attack_events.extend(build_privilege_escalation_scenario(anchors[3], intensity))
    attack_events.extend(build_data_exfiltration_scenario(anchors[4], intensity))

    baseline_target = max(event_count - len(attack_events), 0)
    baseline_events: list[DemoEventSpec] = []
    total_seconds = max(int((now - start).total_seconds()), 1)
    for _ in range(baseline_target):
        hostname, host_ip = rng.choice(BASELINE_HOSTS)
        event_type, source_system, action, message, severity = rng.choice(BASELINE_MESSAGES)
        timestamp = start + timedelta(seconds=rng.randint(0, total_seconds))
        if event_type == "dns":
            dest_ip = "203.0.113.53"
            dest_port = 53
            protocol = "udp"
            raw_log = (
                f'{{"src_ip":"{host_ip}","dest_ip":"{dest_ip}",'
                f'"query":"updates.internal","action":"allowed"}}'
            )
        elif event_type == "authentication":
            dest_ip = None
            dest_port = None
            protocol = None
            raw_log = (
                f'{{"event":"vpn_login",'
                f'"username":"{rng.choice(BASELINE_USERS)}",'
                f'"source_ip":"198.51.100.{rng.randint(10, 90)}"}}'
            )
        else:
            dest_ip = f"10.20.{rng.randint(1, 5)}.{rng.randint(10, 240)}"
            dest_port = rng.choice((80, 443, 8080, 3306, 5432))
            protocol = "tcp"
            raw_log = (
                f"SRC={host_ip} DST={dest_ip} PROTO={protocol.upper()} "
                f"SPT={rng.randint(40000, 65000)} DPT={dest_port} ACTION={action}"
            )

        baseline_events.append(
            DemoEventSpec(
                timestamp=timestamp,
                event_type=event_type,
                source_system=source_system,
                raw_log=raw_log,
                severity=severity,
                source_ip=host_ip,
                dest_ip=dest_ip,
                source_port=rng.randint(40000, 65000) if protocol else None,
                dest_port=dest_port,
                protocol=protocol,
                action=action,
                hostname=hostname,
                username=rng.choice(BASELINE_USERS),
                message=message,
                parsed_data={"scenario": "baseline", "profile": "normal"},
            )
        )

    dataset = [*baseline_events, *attack_events]
    dataset.sort(key=lambda item: item.timestamp)
    return dataset
