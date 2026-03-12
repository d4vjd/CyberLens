# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from cyberlens.analytics.schemas import AnalyticsOverviewResponse
from cyberlens.analytics.service import AnalyticsService
from cyberlens.dependencies import get_db_session

router = APIRouter(prefix="/analytics", tags=["analytics"])


async def get_analytics_service(
    session: AsyncSession = Depends(get_db_session),
) -> AnalyticsService:
    return AnalyticsService(session=session)


@router.get("/status")
async def analytics_status() -> dict[str, str]:
    return {"status": "ready", "message": "Analytics endpoints are available."}


@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def get_overview(
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsOverviewResponse:
    return await service.overview()