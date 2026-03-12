# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from collections.abc import Generator
import os

import pytest
from fastapi.testclient import TestClient

os.environ["STARTUP_TASKS_ENABLED"] = "false"

from cyberlens.config import Settings
from cyberlens.dependencies import get_db_session, get_redis_client, get_settings_dependency
from cyberlens.main import app


class DummySession:
    async def execute(self, _: object) -> None:
        return None


class DummyRedis:
    async def ping(self) -> bool:
        return True


async def override_session() -> Generator[DummySession, None, None]:
    yield DummySession()


async def override_redis() -> Generator[DummyRedis, None, None]:
    yield DummyRedis()


async def override_settings() -> Settings:
    return Settings(debug=False)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_redis_client] = override_redis
    app.dependency_overrides[get_settings_dependency] = override_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()