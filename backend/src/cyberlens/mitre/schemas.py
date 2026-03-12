# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class MitreTechniqueCoverageItem(BaseModel):
    technique_id: str
    name: str
    tactic: str
    description: str
    rule_count: int
    alert_count: int
    last_alert_at: datetime | None


class MitreTacticColumn(BaseModel):
    tactic: str
    techniques: list[MitreTechniqueCoverageItem]


class MitreMatrixResponse(BaseModel):
    generated_at: datetime
    tactics: list[MitreTacticColumn]


class MitreTechniqueDetail(MitreTechniqueCoverageItem):
    rule_ids: list[str]