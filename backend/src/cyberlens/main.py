# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from cyberlens.analytics.router import router as analytics_router
from cyberlens.common.logging import configure_logging
from cyberlens.common.schemas import HealthResponse
from cyberlens.config import Settings, get_settings
from cyberlens.dependencies import get_db_session, get_redis_client, get_settings_dependency
from cyberlens.demo.generator import DemoGenerator
from cyberlens.demo.router import router as demo_router
from cyberlens.detection.engine import DetectionEngine
from cyberlens.detection.rule_loader import RuleLoader
from cyberlens.detection.router import router as detection_router
from cyberlens.incidents.router import router as incidents_router
from cyberlens.ingestion.router import router as ingestion_router
from cyberlens.mitre.router import router as mitre_router
from cyberlens.mitre.service import get_mitre_service
from cyberlens.settings.router import router as settings_router
from cyberlens.settings.service import SettingsService
from cyberlens.streaming.redis_client import build_redis_client
from cyberlens.streaming.websocket import router as websocket_router
from cyberlens.streaming.websocket import alert_hub
from cyberlens.ingestion.syslog_receiver import SyslogReceiver
from cyberlens.db.session import SessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()
    if not settings.startup_tasks_enabled:
        yield
        return

    get_mitre_service().load_bundle()

    async with SessionLocal() as session:
        await RuleLoader().sync_to_database(session)
        await SettingsService(session).ensure_defaults()

    detection_redis = build_redis_client()
    websocket_redis = build_redis_client()
    demo_redis = build_redis_client()
    engine = DetectionEngine(session_factory=SessionLocal, redis=detection_redis)
    demo_generator = DemoGenerator(session_factory=SessionLocal, redis=demo_redis)
    await engine.start()
    await alert_hub.start(websocket_redis)

    receiver = SyslogReceiver(settings)
    await receiver.start()
    async with SessionLocal() as session:
        demo_settings = await SettingsService(session).get_demo_settings()
    if demo_settings.enabled:
        await demo_generator.start(demo_settings.intensity)
        async with SessionLocal() as session:
            await SettingsService(session).set_demo_runtime_state(generator_status="running")
    app.state.syslog_receiver = receiver
    app.state.detection_engine = engine
    app.state.detection_redis = detection_redis
    app.state.websocket_redis = websocket_redis
    app.state.demo_generator = demo_generator
    yield
    await receiver.stop()
    await demo_generator.aclose()
    await alert_hub.stop()
    await engine.stop()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url=f"{settings.api_prefix}/docs",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api_router = APIRouter(prefix=settings.api_prefix)

    @api_router.get("/health", response_model=HealthResponse, tags=["system"])
    async def healthcheck(
        session: AsyncSession = Depends(get_db_session),
        redis: Redis = Depends(get_redis_client),
        _: Settings = Depends(get_settings_dependency),
    ) -> HealthResponse:
        await session.execute(text("SELECT 1"))
        await redis.ping()
        return HealthResponse(status="ok")

    api_router.include_router(ingestion_router)
    api_router.include_router(detection_router)
    api_router.include_router(mitre_router)
    api_router.include_router(incidents_router)
    api_router.include_router(analytics_router)
    api_router.include_router(demo_router)
    api_router.include_router(settings_router)
    app.include_router(api_router)
    app.include_router(websocket_router)
    return app


app = create_app()