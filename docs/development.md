# Development

This guide covers the local development workflow for CyberLens.

## Prerequisites

- **Docker** ≥ 24.0 and **Docker Compose** ≥ 2.20 (Compose plugin)
- **Make** (optional, for shortcut targets)
- **Git** with pre-commit hooks (optional but recommended)

No local Python or Node.js installation is required — all tooling runs inside containers.

## Starting the Dev Stack

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

This starts all services with hot reload:

| Service | Host Port | Notes |
|---|---|---|
| Backend (uvicorn) | `8000` | Auto-reloads on Python file changes |
| Frontend (Vite) | `5173` | HMR enabled |
| nginx | `8080` | Proxies to both services |
| MySQL | — | Accessible only within the Docker network |
| Redis | — | Accessible only within the Docker network |
| Syslog | `5514` | Maps to container port `514` to avoid privileged port friction |

### Source Mounts

The dev override bind-mounts `backend/` and `frontend/` into their respective containers, so file changes on the host are immediately reflected.

## Linting and Testing

```bash
# Run all linters (Ruff, mypy, Bandit) and build-check the frontend
make lint

# Run backend tests with coverage
make test
```

You can also run checks directly:

```bash
# Backend only
docker compose run --rm backend sh -c "ruff check . && ruff format --check . && mypy src && bandit -q -r src"

# Backend tests only
docker compose run --rm backend pytest --cov=src --cov-report=term-missing

# Frontend build check
docker compose run --rm frontend npm run build
```

## Pre-Commit Hooks

The repository includes a `.pre-commit-config.yaml` with Ruff linting/formatting and basic file hygiene hooks. To install:

```bash
pip install pre-commit
pre-commit install
```

Hooks run automatically on `git commit` and catch lint issues before they reach CI.

## Database Migrations

Migrations use Alembic. In the dev stack, `alembic upgrade head` runs automatically on container startup.

To run manually:

```bash
make migrate
# or
docker compose exec backend alembic upgrade head
```

## Syslog Ingestion

- The Compose stack enables the backend syslog listener by default (`SYSLOG_ENABLED=true`).
- The **production** stack exposes `TCP/UDP 514` on the host.
- The **dev** override maps host port `5514` to container port `514` to avoid requiring root permissions.

Test ingestion locally:

```bash
echo "<34>1 2026-03-12T10:00:00Z firewall sshd 1234 - Failed password for root from 10.0.0.5 port 22" \
  | nc -u localhost 5514
```

## Live Baseline Telemetry

When the backend runs in live mode, it can emit a small operational baseline through the real ingestion pipeline. This keeps the console functional before you connect external log sources.

The baseline currently emits:

- MySQL and Redis health probes
- Core service heartbeats
- Routine internal network flows

Check runtime status at:

```bash
curl -s http://localhost/api/v1/ingest/baseline/status
```

## Scenario and Synthetic Data

CyberLens provides three secondary scenario mechanisms for walkthroughs and validation:

### 1. API Seeding

```bash
make seed
# or
curl -s -X POST http://localhost/api/v1/demo/seed \
  -H 'Content-Type: application/json' \
  -d '{"intensity": 6}'
```

This injects a realistic multi-stage attack campaign into the live datastore and detection pipeline.

### 2. Background Generator

Start from the **Settings** page or via API:

```bash
# Start
curl -X POST http://localhost/api/v1/demo/generator/start

# Stop
curl -X POST http://localhost/api/v1/demo/generator/stop
```

The generator continuously produces events, alerts, and cases while running.

### 3. Frontend Synthetic Mode

Toggle from the **Settings** page. Synthetic mode renders a dense local dataset inside the frontend without any backend mutations.
Repository screenshots are captured from this mode using the widescreen desktop layout so the UI stays fully populated.

<img src="assets/settings.png" alt="Settings Mode Toggle" width="100%" />

## Data Clearing

The Settings page exposes two maintenance actions:

- `Clear seeded data` removes only seeded scenario records from the live datastore.
- `Clear live data` removes indexed events, alerts, cases, and linked investigation records so the live baseline can repopulate the environment from a clean slate.

Equivalent API calls:

```bash
curl -X DELETE http://localhost/api/v1/demo/seeded-data
curl -X DELETE http://localhost/api/v1/demo/live-data
```

## Useful Make Targets

| Target | Description |
|---|---|
| `make up` | Build and start the production stack |
| `make down` | Stop services and remove orphans |
| `make build` | Build images without starting |
| `make migrate` | Run Alembic migrations |
| `make seed` | Seed scenario data via REST API |
| `make test` | Run backend tests with coverage |
| `make lint` | Full lint pipeline |
| `make logs` | Tail live logs from all services |
