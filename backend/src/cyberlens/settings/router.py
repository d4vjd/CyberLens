# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from cyberlens.demo.generator import DemoGenerator
from cyberlens.dependencies import get_db_session
from cyberlens.settings.schemas import (
    AnalystSummary,
    DemoSettings,
    DemoSettingsUpdate,
    SettingsStatusResponse,
    SystemConfigItem,
)
from cyberlens.settings.service import SettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


async def get_settings_service(
    session: AsyncSession = Depends(get_db_session),
) -> SettingsService:
    return SettingsService(session=session)


def get_demo_generator(request: Request) -> DemoGenerator | None:
    return getattr(request.app.state, "demo_generator", None)


@router.get("/status", response_model=SettingsStatusResponse)
async def settings_status(
    service: SettingsService = Depends(get_settings_service),
) -> SettingsStatusResponse:
    return await service.get_status()


@router.get("/analysts")
async def list_analysts(
    service: SettingsService = Depends(get_settings_service),
) -> list[AnalystSummary]:
    await service.ensure_defaults()
    return await service.list_analysts()


@router.get("/demo", response_model=DemoSettings)
async def get_demo_settings(
    service: SettingsService = Depends(get_settings_service),
) -> DemoSettings:
    await service.ensure_defaults()
    return await service.get_demo_settings()


@router.patch("/demo", response_model=DemoSettings)
async def update_demo_settings(
    payload: DemoSettingsUpdate,
    service: SettingsService = Depends(get_settings_service),
    runtime: DemoGenerator | None = Depends(get_demo_generator),
) -> DemoSettings:
    updated = await service.update_demo_settings(payload)
    if updated.enabled:
        if runtime is not None:
            await runtime.start(updated.intensity)
        await service.set_demo_runtime_state(generator_status="running")
    else:
        if runtime is not None:
            await runtime.stop()
        await service.set_demo_runtime_state(generator_status="stopped")
    return await service.get_demo_settings()


@router.get("/config", response_model=list[SystemConfigItem])
async def list_config(
    service: SettingsService = Depends(get_settings_service),
) -> list[SystemConfigItem]:
    await service.ensure_defaults()
    return await service.list_configs()
