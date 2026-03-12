# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cyberlens.config import get_settings
from cyberlens.detection.models import DetectionRule, MitreTechniqueCoverage
from cyberlens.mitre.schemas import (
    MitreMatrixResponse,
    MitreTacticColumn,
    MitreTechniqueCoverageItem,
    MitreTechniqueDetail,
)


@dataclass(slots=True)
class TechniqueRecord:
    technique_id: str
    name: str
    description: str
    tactics: list[str]


class MitreAttackService:
    def __init__(self, bundle_path: Path | None = None) -> None:
        self.bundle_path = bundle_path or get_settings().resolved_mitre_bundle_path
        self.techniques: dict[str, TechniqueRecord] = {}

    @property
    def technique_count(self) -> int:
        return len(self.techniques)

    def load_bundle(self) -> None:
        with self.bundle_path.open("r", encoding="utf-8") as handle:
            bundle = json.load(handle)

        techniques: dict[str, TechniqueRecord] = {}
        for obj in bundle.get("objects", []):
            if obj.get("type") != "attack-pattern":
                continue
            external_refs = obj.get("external_references", [])
            technique_ref = next(
                (ref for ref in external_refs if ref.get("source_name") == "mitre-attack"),
                None,
            )
            if not technique_ref:
                continue
            technique_id = technique_ref["external_id"]
            techniques[technique_id] = TechniqueRecord(
                technique_id=technique_id,
                name=obj.get("name", technique_id),
                description=obj.get("description", ""),
                tactics=obj.get("x_mitre_tactic_type") or obj.get("kill_chain_phases_tactics") or obj.get("x_mitre_tactics") or [],
            )

            if not techniques[technique_id].tactics:
                phases = obj.get("kill_chain_phases", [])
                techniques[technique_id].tactics = [
                    phase.get("phase_name", "").replace("-", " ") for phase in phases if phase.get("phase_name")
                ]
        self.techniques = techniques

    async def build_matrix(self, session: AsyncSession) -> MitreMatrixResponse:
        coverage_rows = (
            await session.execute(
                select(
                    MitreTechniqueCoverage.technique_id,
                    MitreTechniqueCoverage.tactic,
                    func.sum(MitreTechniqueCoverage.alert_count),
                    func.max(MitreTechniqueCoverage.last_alert_at),
                ).group_by(MitreTechniqueCoverage.technique_id, MitreTechniqueCoverage.tactic)
            )
        ).all()
        coverage_map = {
            (technique_id, tactic): {
                "alert_count": int(alert_count or 0),
                "last_alert_at": last_alert_at,
            }
            for technique_id, tactic, alert_count, last_alert_at in coverage_rows
        }

        rule_rows = (
            await session.execute(
                select(
                    DetectionRule.mitre_technique_id,
                    DetectionRule.mitre_tactic,
                    func.count(DetectionRule.id),
                )
                .where(DetectionRule.enabled.is_(True))
                .group_by(DetectionRule.mitre_technique_id, DetectionRule.mitre_tactic)
            )
        ).all()
        rule_map = {
            (technique_id, tactic): int(rule_count or 0)
            for technique_id, tactic, rule_count in rule_rows
            if technique_id and tactic
        }

        columns: dict[str, list[MitreTechniqueCoverageItem]] = defaultdict(list)
        for technique_id, technique in self.techniques.items():
            for tactic in technique.tactics:
                normalized_tactic = tactic.replace("_", "-").lower()
                coverage = coverage_map.get((technique_id, normalized_tactic), {})
                rule_count = rule_map.get((technique_id, normalized_tactic), 0)
                columns[normalized_tactic].append(
                    MitreTechniqueCoverageItem(
                        technique_id=technique_id,
                        name=technique.name,
                        tactic=normalized_tactic,
                        description=technique.description,
                        rule_count=rule_count,
                        alert_count=int(coverage.get("alert_count", 0)),
                        last_alert_at=coverage.get("last_alert_at"),
                    )
                )

        ordered = [
            MitreTacticColumn(
                tactic=tactic,
                techniques=sorted(items, key=lambda item: item.technique_id),
            )
            for tactic, items in sorted(columns.items())
        ]
        return MitreMatrixResponse(generated_at=datetime.now(UTC), tactics=ordered)

    async def get_technique_detail(
        self,
        session: AsyncSession,
        technique_id: str,
    ) -> MitreTechniqueDetail:
        technique = self.techniques.get(technique_id)
        if technique is None:
            raise HTTPException(status_code=404, detail="Technique not found")

        rules = (
            await session.scalars(
                select(DetectionRule).where(DetectionRule.mitre_technique_id == technique_id)
            )
        ).all()
        coverage = (
            await session.execute(
                select(
                    func.sum(MitreTechniqueCoverage.alert_count),
                    func.max(MitreTechniqueCoverage.last_alert_at),
                ).where(MitreTechniqueCoverage.technique_id == technique_id)
            )
        ).one()

        return MitreTechniqueDetail(
            technique_id=technique_id,
            name=technique.name,
            tactic=", ".join(technique.tactics),
            description=technique.description,
            rule_count=len(rules),
            alert_count=int(coverage[0] or 0),
            last_alert_at=coverage[1],
            rule_ids=[rule.rule_id for rule in rules],
        )


_mitre_service = MitreAttackService()


def get_mitre_service() -> MitreAttackService:
    return _mitre_service