# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cyberlens.config import get_settings
from cyberlens.incidents.models import Case
from cyberlens.settings.models import Analyst, AnalystRole, SystemConfig
from cyberlens.settings.schemas import (
    AnalystSummary,
    DemoSettings,
    DemoSettingsUpdate,
    SettingsStatusResponse,
    SystemConfigItem,
)

DEMO_CONFIG_KEY = "demo_mode"


class SettingsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def ensure_defaults(self) -> None:
        analyst_count = int(
            (await self.session.scalar(select(func.count()).select_from(Analyst))) or 0
        )
        if analyst_count == 0:
            self.session.add_all(
                [
                    Analyst(
                        username="ahassan",
                        display_name="Amira Hassan",
                        role=AnalystRole.SOC_ANALYST,
                        email="amira.hassan@cyberlens.local",
                    ),
                    Analyst(
                        username="mreyes",
                        display_name="Marcus Reyes",
                        role=AnalystRole.INCIDENT_COMMANDER,
                        email="marcus.reyes@cyberlens.local",
                    ),
                    Analyst(
                        username="sclark",
                        display_name="Sophia Clark",
                        role=AnalystRole.VULNERABILITY_ANALYST,
                        email="sophia.clark@cyberlens.local",
                    ),
                ]
            )

        existing = await self.session.scalar(
            select(SystemConfig).where(SystemConfig.config_key == DEMO_CONFIG_KEY)
        )
        if existing is None:
            settings = get_settings()
            self.session.add(
                SystemConfig(
                    config_key=DEMO_CONFIG_KEY,
                    config_value={
                        "enabled": False,
                        "intensity": settings.demo_default_intensity,
                        "mode": "live",
                        "generator_status": "stopped",
                    },
                    description="Demo mode and synthetic generation settings",
                )
            )

        await self.session.commit()

    async def list_analysts(self) -> list[AnalystSummary]:
        analysts = (
            await self.session.scalars(select(Analyst).order_by(Analyst.display_name))
        ).all()
        summaries: list[AnalystSummary] = []
        for analyst in analysts:
            active_cases = int(
                (
                    await self.session.scalar(
                        select(func.count())
                        .select_from(Case)
                        .where(
                            (Case.assigned_to == analyst.username)
                            | (Case.assigned_to == analyst.display_name)
                        )
                    )
                )
                or 0
            )
            summaries.append(
                AnalystSummary.model_validate(analyst).model_copy(
                    update={"active_cases": active_cases}
                )
            )
        return summaries

    async def get_demo_settings(self) -> DemoSettings:
        config = await self._get_or_create_demo_config()
        return DemoSettings.model_validate(config.config_value)

    async def update_demo_settings(self, payload: DemoSettingsUpdate) -> DemoSettings:
        config = await self._get_or_create_demo_config()
        current = dict(config.config_value)
        if payload.enabled is not None:
            current["enabled"] = payload.enabled
        if payload.intensity is not None:
            current["intensity"] = payload.intensity
        if payload.mode is not None:
            current["mode"] = payload.mode
        config.config_value = current
        await self.session.commit()
        return DemoSettings.model_validate(config.config_value)

    async def set_demo_runtime_state(self, **updates: Any) -> DemoSettings:
        config = await self._get_or_create_demo_config()
        current = dict(config.config_value)
        current.update(updates)
        config.config_value = current
        await self.session.commit()
        return DemoSettings.model_validate(config.config_value)

    async def list_configs(self) -> list[SystemConfigItem]:
        configs = (
            await self.session.scalars(select(SystemConfig).order_by(SystemConfig.config_key))
        ).all()
        return [
            SystemConfigItem(
                key=item.config_key, value=item.config_value, description=item.description
            )
            for item in configs
        ]

    async def get_status(self) -> SettingsStatusResponse:
        await self.ensure_defaults()
        return SettingsStatusResponse(
            analysts=await self.list_analysts(),
            demo=await self.get_demo_settings(),
            configs=await self.list_configs(),
        )

    async def _get_or_create_demo_config(self) -> SystemConfig:
        config = await self.session.scalar(
            select(SystemConfig).where(SystemConfig.config_key == DEMO_CONFIG_KEY)
        )
        if config is None:
            await self.ensure_defaults()
            config = await self.session.scalar(
                select(SystemConfig).where(SystemConfig.config_key == DEMO_CONFIG_KEY)
            )
            if config is None:
                raise RuntimeError("Config should not be None after upsert")
        return config
