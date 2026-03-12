# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from cyberlens.dependencies import get_db_session
from cyberlens.mitre.schemas import MitreMatrixResponse, MitreTechniqueDetail
from cyberlens.mitre.service import MitreAttackService, get_mitre_service

router = APIRouter(tags=["mitre"])


@router.get("/mitre/status")
async def mitre_status(
    service: MitreAttackService = Depends(get_mitre_service),
) -> dict[str, str]:
    return {
        "status": "ready",
        "message": f"Loaded {service.technique_count} MITRE techniques into memory.",
    }


@router.get("/mitre/matrix", response_model=MitreMatrixResponse)
async def get_matrix(
    session: AsyncSession = Depends(get_db_session),
    service: MitreAttackService = Depends(get_mitre_service),
) -> MitreMatrixResponse:
    return await service.build_matrix(session)


@router.get("/mitre/techniques/{technique_id}", response_model=MitreTechniqueDetail)
async def get_technique(
    technique_id: str,
    session: AsyncSession = Depends(get_db_session),
    service: MitreAttackService = Depends(get_mitre_service),
) -> MitreTechniqueDetail:
    return await service.get_technique_detail(session, technique_id)