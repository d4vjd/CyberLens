# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from datetime import UTC, datetime

from cyberlens.main import app
from cyberlens.settings.router import get_settings_service
from cyberlens.settings.schemas import AnalystSummary, DemoSettings, SettingsStatusResponse, SystemConfigItem
from cyberlens.settings.service import SettingsService
from cyberlens.settings.models import AnalystRole


class FakeSettingsService:
    async def get_status(self):
        return SettingsStatusResponse(
            analysts=[
                AnalystSummary(
                    username="ahassan",
                    display_name="Amira Hassan",
                    role=AnalystRole.SOC_ANALYST,
                    email="amira.hassan@cyberlens.local",
                    is_active=True,
                    active_cases=2,
                )
            ],
            demo=DemoSettings(
                enabled=True,
                intensity=6,
                mode="live",
                seeded_at=datetime(2026, 3, 12, 15, 0, tzinfo=UTC),
                generator_status="running",
            ),
            configs=[
                SystemConfigItem(
                    key="demo_mode",
                    value={"enabled": True},
                    description="Demo settings",
                )
            ],
        )

    async def ensure_defaults(self) -> None:
        return None

    async def list_analysts(self):
        return (await self.get_status()).analysts

    async def get_demo_settings(self):
        return (await self.get_status()).demo

    async def update_demo_settings(self, payload):
        del payload
        return (await self.get_status()).demo

    async def list_configs(self):
        return (await self.get_status()).configs

    async def set_demo_runtime_state(self, **updates):
        del updates
        return (await self.get_status()).demo


async def override_settings_service():
    return FakeSettingsService()


def test_settings_status_endpoint(client) -> None:
    app.dependency_overrides[get_settings_service] = override_settings_service
    response = client.get("/api/v1/settings/status")
    app.dependency_overrides.pop(get_settings_service, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["analysts"][0]["username"] == "ahassan"
    assert payload["demo"]["generator_status"] == "running"


def test_settings_demo_patch_endpoint(client) -> None:
    app.dependency_overrides[get_settings_service] = override_settings_service
    response = client.patch("/api/v1/settings/demo", json={"enabled": True, "intensity": 6})
    app.dependency_overrides.pop(get_settings_service, None)

    assert response.status_code == 200
    assert response.json()["enabled"] is True