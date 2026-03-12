# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from cyberlens.dependencies import get_db_session, get_redis_client
from cyberlens.ingestion.schemas import (
    EventDetail,
    EventListResponse,
    EventQueryParams,
    IngestBatchRequest,
    IngestResponse,
    IngestSingleRequest,
)
from cyberlens.ingestion.service import IngestionService

router = APIRouter(tags=["ingestion"])


async def get_ingestion_service(
    session: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis_client),
) -> IngestionService:
    return IngestionService(session=session, redis=redis)


@router.get("/ingest/status")
async def ingestion_status() -> dict[str, str]:
    return {"status": "ready", "message": "Ingestion pipeline is available."}


@router.post("/ingest/raw", response_model=IngestResponse)
async def ingest_raw_log(
    payload: IngestSingleRequest,
    service: IngestionService = Depends(get_ingestion_service),
) -> IngestResponse:
    return await service.ingest_batch([payload])


@router.post("/ingest/batch", response_model=IngestResponse)
async def ingest_batch_logs(
    payload: IngestBatchRequest,
    service: IngestionService = Depends(get_ingestion_service),
) -> IngestResponse:
    return await service.ingest_batch(payload.logs)


@router.get("/events", response_model=EventListResponse)
async def list_events(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    event_type: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    source_ip: str | None = Query(default=None),
    dest_ip: str | None = Query(default=None),
    source_system: str | None = Query(default=None),
    action: str | None = Query(default=None),
    search: str | None = Query(default=None),
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    service: IngestionService = Depends(get_ingestion_service),
) -> EventListResponse:
    params = EventQueryParams(
        offset=offset,
        limit=limit,
        event_type=event_type,
        severity=severity,
        source_ip=source_ip,
        dest_ip=dest_ip,
        source_system=source_system,
        action=action,
        search=search,
        start_time=start_time,
        end_time=end_time,
    )
    return await service.list_events(params)


@router.get("/events/{event_id}", response_model=EventDetail)
async def get_event(
    event_id: int,
    service: IngestionService = Depends(get_ingestion_service),
) -> EventDetail:
    return await service.get_event(event_id)