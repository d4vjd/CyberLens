# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

from __future__ import annotations

from collections import Counter

from fastapi import HTTPException
from redis.asyncio import Redis
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from cyberlens.ingestion.models import Event, SeverityLevel
from cyberlens.ingestion.pipeline import LogIngestionPipeline
from cyberlens.ingestion.schemas import (
    EventDetail,
    EventListResponse,
    EventQueryParams,
    IngestResponse,
    IngestSingleRequest,
    IngestedEventSummary,
)
from cyberlens.streaming.publisher import publish_events


class IngestionService:
    def __init__(
        self,
        session: AsyncSession,
        redis: Redis,
        pipeline: LogIngestionPipeline | None = None,
    ) -> None:
        self.session = session
        self.redis = redis
        self.pipeline = pipeline or LogIngestionPipeline()

    async def ingest_batch(self, payloads: list[IngestSingleRequest]) -> IngestResponse:
        persisted: list[tuple[Event, str]] = []
        parser_counts: Counter[str] = Counter()

        try:
            for start in range(0, len(payloads), 500):
                chunk = payloads[start : start + 500]
                batch: list[tuple[Event, str]] = [self.pipeline.process(payload) for payload in chunk]
                for event, _ in batch:
                    self.session.add(event)
                await self.session.flush()
                persisted.extend(batch)
                parser_counts.update(parser_name for _, parser_name in batch)

            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        await publish_events(self.redis, [event for event, _ in persisted])

        return IngestResponse(
            ingested_count=len(persisted),
            parser_counts=dict(parser_counts),
            events=[
                IngestedEventSummary(
                    id=event.id,
                    timestamp=event.timestamp,
                    event_type=event.event_type,
                    source_system=event.source_system,
                    parser_name=parser_name,
                )
                for event, parser_name in persisted
            ],
        )

    async def list_events(self, params: EventQueryParams) -> EventListResponse:
        stmt = select(Event)

        if params.event_type:
            stmt = stmt.where(Event.event_type == params.event_type)
        if params.severity:
            stmt = stmt.where(Event.severity == SeverityLevel(params.severity))
        if params.source_ip:
            stmt = stmt.where(Event.source_ip == params.source_ip)
        if params.dest_ip:
            stmt = stmt.where(Event.dest_ip == params.dest_ip)
        if params.source_system:
            stmt = stmt.where(Event.source_system == params.source_system)
        if params.action:
            stmt = stmt.where(Event.action == params.action.lower())
        if params.start_time:
            stmt = stmt.where(Event.timestamp >= params.start_time)
        if params.end_time:
            stmt = stmt.where(Event.timestamp <= params.end_time)
        if params.search:
            search_term = f"%{params.search}%"
            stmt = stmt.where(
                or_(
                    Event.message.ilike(search_term),
                    Event.raw_log.ilike(search_term),
                    Event.hostname.ilike(search_term),
                    Event.username.ilike(search_term),
                )
            )

        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = int((await self.session.scalar(total_stmt)) or 0)

        results = await self.session.scalars(
            stmt.order_by(Event.timestamp.desc()).offset(params.offset).limit(params.limit)
        )
        items = [EventDetail.model_validate(event) for event in results.all()]
        return EventListResponse(
            items=items,
            total=total,
            offset=params.offset,
            limit=params.limit,
        )

    async def get_event(self, event_id: int) -> EventDetail:
        event = await self.session.get(Event, event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")
        return EventDetail.model_validate(event)