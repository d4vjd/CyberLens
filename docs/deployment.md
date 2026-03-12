<![CDATA[# Deployment

CyberLens is deployed as a Docker Compose stack. This document covers both production-like and development deployments.

## Production Stack

```bash
docker compose up --build
```

This starts all five services (`mysql`, `redis`, `backend`, `frontend`, `nginx`) with:

- nginx on port `80`, proxying `/api/*` to the backend and serving the frontend static build.
- Backend syslog listener on `TCP/UDP 514`.
- MySQL and Redis data persisted to named Docker volumes (`mysql_data`, `redis_data`).
- Healthchecks on MySQL, Redis, and the backend ensuring services start in dependency order.

### Environment Variables

Copy `.env.example` to `.env` to override defaults. Key variables:

| Variable | Default | Description |
|---|---|---|
| `MYSQL_ROOT_PASSWORD` | `root` | MySQL root password |
| `MYSQL_DATABASE` | `cyberlens` | Database name |
| `MYSQL_USER` | `cyberlens` | Application database user |
| `MYSQL_PASSWORD` | `cyberlens` | Application database password |
| `APP_ENV` | `development` | Application environment label |
| `DEBUG` | `true` | Enable debug logging |
| `REDIS_EVENT_STREAM` | `cyberlens:events` | Redis stream key for ingested events |
| `SYSLOG_ENABLED` | `false` (`.env.example`) / `true` (compose) | Enable syslog listener |
| `RULES_PATH` | `../rules` / `/app/rules` | Path to YAML detection rules |
| `MITRE_BUNDLE_PATH` | (see `.env.example`) | Path to ATT&CK bundle JSON |

> **Note**: The defaults in `.env.example` are for local development only. Replace all credentials before exposing CyberLens to any network.

## Development Stack

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

The dev override adds:

- **Backend hot reload** — source directory bind-mounted with uvicorn `--reload`.
- **Frontend HMR** — source directory bind-mounted with Vite dev server on port `5173`.
- **Host-accessible ports** — backend on `8000`, frontend on `5173`, nginx on `8080`, syslog on `5514`.
- **Automatic dependency install** — `pip install -e .[dev]` and `npm install` run on container start.

## Volumes

| Volume | Service | Purpose |
|---|---|---|
| `mysql_data` | mysql | Persistent database storage |
| `redis_data` | redis | Redis data (persistence disabled by default) |

## Health Checks

All critical services include Docker healthchecks:

- **MySQL**: `mysqladmin ping` every 10 s, 12 retries.
- **Redis**: `redis-cli ping` every 10 s, 12 retries.
- **Backend**: HTTP `GET /api/v1/health` every 20 s, 6 retries.

The backend depends on healthy MySQL and Redis. The frontend depends on a healthy backend. nginx depends on both.

## Stopping

```bash
docker compose down              # stop and remove containers
docker compose down -v           # also remove named volumes (resets database)
```
]]>
