# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

import asyncio
import random
from contextlib import suppress
from datetime import datetime, timedelta

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from cyberlens.common.time_utils import utc_now
from cyberlens.demo.service import DemoService
from cyberlens.demo.types import DemoEventSpec
from cyberlens.ingestion.models import SeverityLevel


class DemoGenerator:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession], redis: Redis) -> None:
        self.session_factory = session_factory
        self.redis = redis
        self._task: asyncio.Task[None] | None = None
        self._running = False
        self._intensity = 5
        self._rng = random.Random(20260312)  # nosec B311
        self._attack_step = 0

    @property
    def intensity(self) -> int:
        return self._intensity

    @property
    def is_running(self) -> bool:
        return self._running

    async def start(self, intensity: int) -> None:
        self._intensity = max(1, min(10, intensity))
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run(), name="cyberlens-demo-generator")

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def aclose(self) -> None:
        await self.stop()
        await self.redis.aclose()

    async def _run(self) -> None:
        while self._running:
            events_per_second = 1 + round((self._intensity - 1) * (49 / 9))
            events_per_tick = max(1, min(10, self._intensity))
            delay = max(events_per_tick / events_per_second, 0.1)
            specs = self._build_tick_specs(events_per_tick)
            async with self.session_factory() as session:
                service = DemoService(session=session, redis=self.redis)
                await service.ingest_specs(specs)
            await asyncio.sleep(delay)

    def _build_tick_specs(self, events_per_tick: int) -> list[DemoEventSpec]:
        baseline_count = max(1, int(events_per_tick * 0.8))
        attack_count = max(1, events_per_tick - baseline_count)
        now = utc_now()
        specs = [self._build_baseline_event(now) for _ in range(baseline_count)]
        specs.extend(self._build_attack_events(now, attack_count))
        specs.sort(key=lambda item: item.timestamp)
        return specs

    def _build_attack_events(self, timestamp: datetime, attack_count: int) -> list[DemoEventSpec]:
        builders = (
            self._build_scan_fragment,
            self._build_brute_force_fragment,
            self._build_lateral_fragment,
            self._build_privilege_fragment,
            self._build_exfil_fragment,
        )
        builder = builders[self._attack_step % len(builders)]
        self._attack_step += 1
        return [builder(timestamp, index) for index in range(attack_count)]

    def _build_baseline_event(self, timestamp: datetime) -> DemoEventSpec:
        hostnames = (
            ("web-prod-01", "10.20.1.10"),
            ("api-prod-02", "10.20.1.22"),
            ("db-prod-01", "10.20.3.11"),
        )
        hostname, source_ip = self._rng.choice(hostnames)
        dest_ip = f"10.20.{self._rng.randint(1, 5)}.{self._rng.randint(10, 200)}"
        dest_port = self._rng.choice((80, 443, 8080, 3306))
        action = self._rng.choice(("allowed", "success"))
        event_type = "network" if action == "allowed" else "authentication"
        source_system = "firewall" if event_type == "network" else "vpn"
        return DemoEventSpec(
            timestamp=timestamp,
            event_type=event_type,
            source_system=source_system,
            raw_log=(
                f"SRC={source_ip} DST={dest_ip} PROTO=TCP SPT={self._rng.randint(40000, 65000)} "
                f"DPT={dest_port} ACTION={action}"
            ),
            severity=SeverityLevel.LOW,
            source_ip=source_ip,
            dest_ip=dest_ip,
            source_port=self._rng.randint(40000, 65000),
            dest_port=dest_port,
            protocol="tcp",
            action=action,
            hostname=hostname,
            username=self._rng.choice(("jmartin", "alee", "svc-web")),
            message="Synthetic baseline heartbeat event",
            parsed_data={"scenario": "generator", "profile": "baseline"},
        )

    def _build_scan_fragment(self, timestamp: datetime, index: int) -> DemoEventSpec:
        port = (20 + self._attack_step + index) % 10000
        return DemoEventSpec(
            timestamp=timestamp + timedelta(milliseconds=index * 200),
            event_type="network",
            source_system="netflow",
            raw_log=(
                f"SRC=203.0.113.17 DST=10.20.1.44 PROTO=TCP "
                f"SPT={40200 + index} DPT={port} FLAGS=SYN"
            ),
            severity=SeverityLevel.MEDIUM,
            source_ip="203.0.113.17",
            dest_ip="10.20.1.44",
            source_port=40200 + index,
            dest_port=port,
            protocol="tcp",
            action="allowed",
            hostname="web-prod-01",
            message="Synthetic scan fragment",
            parsed_data={"scenario": "generator", "attack": "port_scan"},
        )

    def _build_brute_force_fragment(self, timestamp: datetime, index: int) -> DemoEventSpec:
        port = 51100 + ((self._attack_step + index) % 200)
        return DemoEventSpec(
            timestamp=timestamp + timedelta(milliseconds=index * 250),
            event_type="authentication",
            source_system="sshd",
            raw_log=(
                f"<34>Mar 12 09:10:{index:02d} bastion-edge-01 sshd[22{index:02d}]: "
                f"Failed password for invalid user admin from 198.51.100.42 port {port} ssh2"
            ),
            severity=SeverityLevel.HIGH,
            source_ip="198.51.100.42",
            dest_ip="10.20.3.12",
            source_port=port,
            dest_port=22,
            protocol="tcp",
            action="failed",
            hostname="bastion-edge-01",
            username="admin",
            message="Synthetic brute-force fragment",
            parsed_data={"scenario": "generator", "attack": "brute_force"},
        )

    def _build_lateral_fragment(self, timestamp: datetime, index: int) -> DemoEventSpec:
        return DemoEventSpec(
            timestamp=timestamp + timedelta(milliseconds=index * 300),
            event_type="network",
            source_system="windows",
            raw_log=(
                f"SRC=10.20.4.88 DST=10.20.5.{14 + index} PROTO=TCP "
                f"SPT={41000 + index} DPT=445 ACTION=allowed"
            ),
            severity=SeverityLevel.HIGH,
            source_ip="10.20.4.88",
            dest_ip=f"10.20.5.{14 + index}",
            source_port=41000 + index,
            dest_port=445,
            protocol="tcp",
            action="allowed",
            hostname="wks-finance-14",
            username="svc-backup",
            message="Synthetic SMB pivot fragment",
            parsed_data={"scenario": "generator", "attack": "lateral_movement"},
        )

    def _build_privilege_fragment(self, timestamp: datetime, index: int) -> DemoEventSpec:
        del index
        return DemoEventSpec(
            timestamp=timestamp,
            event_type="process",
            source_system="linux",
            raw_log="sudo: svc-backup : TTY=pts/2 ; PWD=/tmp ; USER=root ; COMMAND=/bin/bash",
            severity=SeverityLevel.CRITICAL,
            source_ip="10.20.5.14",
            action="executed",
            hostname="linux-batch-03",
            username="svc-backup",
            message="Synthetic sudo escalation fragment",
            parsed_data={"scenario": "generator", "attack": "privilege_escalation"},
        )

    def _build_exfil_fragment(self, timestamp: datetime, index: int) -> DemoEventSpec:
        return DemoEventSpec(
            timestamp=timestamp + timedelta(milliseconds=index * 150),
            event_type="dns",
            source_system="firewall",
            raw_log=(
                f'{{"src_ip":"10.20.5.14","dest_ip":"203.0.113.91","query":"chunk-{index}.demo.local","type":"TXT"}}'
            ),
            severity=SeverityLevel.CRITICAL,
            source_ip="10.20.5.14",
            dest_ip="203.0.113.91",
            source_port=54000 + index,
            dest_port=53,
            protocol="udp",
            action="allowed",
            hostname="linux-batch-03",
            username="svc-backup",
            message="Synthetic DNS exfiltration fragment",
            parsed_data={"scenario": "generator", "attack": "data_exfiltration"},
        )
