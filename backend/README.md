<![CDATA[# CyberLens Backend

FastAPI service powering the CyberLens SIEM application.

## Overview

The backend handles log ingestion, event normalisation, real-time detection, MITRE ATT&CK coverage, incident response workflows, analytics, baseline operational telemetry, and secondary scenario tooling. It connects to MySQL for persistence and Redis for event streaming and stateful detection primitives.

## Module Layout

```
src/cyberlens/
├── analytics/      # Trend and overview analytics endpoints
├── common/         # Shared utilities and helpers
├── db/             # SQLAlchemy models, session factory, and schema
├── demo/           # Scenario seeding, synthetic generator, and data clearing
├── detection/      # Rule engine, evaluators, and rule CRUD
├── incidents/      # Case management, playbooks, evidence, response actions
├── ingestion/      # Parser registry, ingest endpoints, and live baseline emitter
├── mitre/          # ATT&CK bundle loader and coverage API
├── settings/       # Analyst roster and system config
├── streaming/      # Redis stream consumer and WebSocket bridge
├── config.py       # Pydantic settings (reads env vars)
├── dependencies.py # FastAPI dependency injection
└── main.py         # App factory, lifespan hooks, and router mounting
```

## Running Locally (inside Docker)

The backend is designed to run inside the Compose stack. See the [root README](../README.md) for startup instructions.

For development with hot reload:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build backend
```

## Database Migrations

Migrations use Alembic. To apply:

```bash
make migrate
# or directly:
docker compose exec backend alembic upgrade head
```

## Tests

```bash
make test
# or directly:
docker compose run --rm backend pytest --cov=src --cov-report=term-missing
```

## Live Baseline Telemetry

In live mode, the backend can emit low-volume operational telemetry through the same ingestion service used for external logs. The baseline emitter currently produces:

- MySQL and Redis health probes
- Routine service heartbeats for core platform components
- Normal service-to-service network flows

The emitter status is exposed through `GET /api/v1/ingest/baseline/status`.

## Scenario Data Operations

Scenario tooling remains available for walkthroughs, but it is separate from the primary live path:

- `POST /api/v1/demo/seed` seeds a realistic attack chain into the live datastore
- `POST /api/v1/demo/generator/start` and `/stop` control the background synthetic generator
- `DELETE /api/v1/demo/seeded-data` removes only seeded scenario records
- `DELETE /api/v1/demo/live-data` clears indexed live data so the baseline can repopulate clean telemetry

## Linting

```bash
make lint
# or directly:
docker compose run --rm backend sh -c "ruff check . && ruff format --check . && mypy src && bandit -q -r src"
```

## Key Dependencies

| Package | Purpose |
|---|---|
| FastAPI | Async HTTP framework |
| SQLAlchemy 2.0 | Async ORM and query builder |
| Alembic | Database migration management |
| Pydantic / pydantic-settings | Request/response validation and config |
| Redis (hiredis) | Event streaming and detection state |
| structlog | Structured logging |
| PyYAML | Rule and playbook parsing |
| mitreattack-python | ATT&CK bundle handling |
| uvicorn | ASGI server |
]]>
