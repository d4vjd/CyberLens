# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from cyberlens.demo.generator import DemoGenerator
from cyberlens.demo.schemas import DemoGeneratorRequest, DemoSeedRequest, DemoSeedResponse, DemoStatusResponse
from cyberlens.demo.service import DemoService
from cyberlens.dependencies import get_db_session, get_redis_client
from cyberlens.settings.schemas import DemoSettingsUpdate
from cyberlens.settings.service import SettingsService

router = APIRouter(prefix="/demo", tags=["demo"])


async def get_demo_service(
    session: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis_client),
) -> DemoService:
    return DemoService(session=session, redis=redis)


def get_demo_generator(request: Request) -> DemoGenerator | None:
    return getattr(request.app.state, "demo_generator", None)


@router.get("/status", response_model=DemoStatusResponse)
async def demo_status(
    service: DemoService = Depends(get_demo_service),
) -> DemoStatusResponse:
    return await service.get_status()


@router.post("/seed", response_model=DemoSeedResponse)
async def seed_demo_data(
    payload: DemoSeedRequest,
    service: DemoService = Depends(get_demo_service),
) -> DemoSeedResponse:
    return await service.seed_dataset(payload)


@router.post("/generator/start", response_model=DemoStatusResponse)
async def start_demo_generator(
    payload: DemoGeneratorRequest,
    session: AsyncSession = Depends(get_db_session),
    service: DemoService = Depends(get_demo_service),
    runtime: DemoGenerator | None = Depends(get_demo_generator),
) -> DemoStatusResponse:
    settings_service = SettingsService(session)
    await settings_service.ensure_defaults()
    await settings_service.update_demo_settings(
        DemoSettingsUpdate(enabled=True, intensity=payload.intensity)
    )
    if runtime is not None:
        await runtime.start(payload.intensity)
    await settings_service.set_demo_runtime_state(generator_status="running")
    return await service.get_status()


@router.post("/generator/stop", response_model=DemoStatusResponse)
async def stop_demo_generator(
    session: AsyncSession = Depends(get_db_session),
    service: DemoService = Depends(get_demo_service),
    runtime: DemoGenerator | None = Depends(get_demo_generator),
) -> DemoStatusResponse:
    settings_service = SettingsService(session)
    await settings_service.ensure_defaults()
    await settings_service.update_demo_settings(
        DemoSettingsUpdate(enabled=False)
    )
    if runtime is not None:
        await runtime.stop()
    await settings_service.set_demo_runtime_state(generator_status="stopped")
    return await service.get_status()