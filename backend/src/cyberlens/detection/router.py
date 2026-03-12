# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from cyberlens.dependencies import get_db_session, get_redis_client
from cyberlens.detection.rule_loader import RuleLoader
from cyberlens.detection.schemas import (
    AlertDetail,
    AlertListResponse,
    RuleHistoricalTestRequest,
    RuleHistoricalTestResponse,
    RuleMutationRequest,
    RuleMutationResponse,
    RuleSummary,
    RuleSyncResponse,
)
from cyberlens.detection.service import DetectionService

router = APIRouter(tags=["detection"])


async def get_detection_service(
    session: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis_client),
) -> DetectionService:
    return DetectionService(session=session, redis=redis)


@router.get("/detection/status")
async def detection_status() -> dict[str, str]:
    return {"status": "ready", "message": "Detection engine is running."}


@router.post("/detection/rules/reload", response_model=RuleSyncResponse)
async def reload_rules(
    session: AsyncSession = Depends(get_db_session),
) -> RuleSyncResponse:
    loader = RuleLoader()
    return await loader.sync_to_database(session)


@router.get("/rules", response_model=list[RuleSummary])
async def list_rules(
    service: DetectionService = Depends(get_detection_service),
) -> list[RuleSummary]:
    return await service.list_rules()


@router.post("/rules", response_model=RuleMutationResponse)
async def save_rule(
    payload: RuleMutationRequest,
    service: DetectionService = Depends(get_detection_service),
) -> RuleMutationResponse:
    return await service.save_rule_yaml(payload.yaml)


@router.patch("/rules/{rule_id}", response_model=RuleMutationResponse)
async def update_rule(
    rule_id: str,
    payload: RuleMutationRequest,
    service: DetectionService = Depends(get_detection_service),
) -> RuleMutationResponse:
    del rule_id
    return await service.save_rule_yaml(payload.yaml)


@router.delete("/rules/{rule_id}", response_model=RuleMutationResponse)
async def retire_rule(
    rule_id: str,
    service: DetectionService = Depends(get_detection_service),
) -> RuleMutationResponse:
    return await service.retire_rule(rule_id)


@router.post("/rules/test", response_model=RuleHistoricalTestResponse)
async def test_rule(
    payload: RuleHistoricalTestRequest,
    service: DetectionService = Depends(get_detection_service),
) -> RuleHistoricalTestResponse:
    return await service.test_rule_yaml(payload.yaml, limit=payload.limit)


@router.get("/alerts", response_model=AlertListResponse)
async def list_alerts(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    service: DetectionService = Depends(get_detection_service),
) -> AlertListResponse:
    return await service.list_alerts(offset=offset, limit=limit)


@router.get("/alerts/{alert_id}", response_model=AlertDetail)
async def get_alert(
    alert_id: int,
    service: DetectionService = Depends(get_detection_service),
) -> AlertDetail:
    return await service.get_alert(alert_id)