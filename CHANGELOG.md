<![CDATA[# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-12

### Added

- **Backend**: FastAPI application with async SQLAlchemy, Pydantic settings, structlog, and `GET /api/v1/health`.
- **Ingestion**: Raw and batch log intake endpoints with a parser registry supporting syslog, Windows events, firewall logs, NetFlow, JSON, and generic text.
- **Events**: Paginated event listing with search, time range, and multi-field filtering.
- **Syslog Receiver**: UDP/TCP syslog listener wired into the Compose stack.
- **Detection Engine**: Redis Stream-backed rule evaluation with threshold, pattern, sequence, and aggregation evaluators.
- **Rule Management**: YAML rule sync from `rules/` at startup, REST endpoints for CRUD operations, and historical test-against-telemetry support.
- **MITRE ATT&CK**: In-memory ATT&CK subset bundle with API-backed matrix coverage derived from live rules and alerts.
- **Incident Response**: Case creation, alert escalation, comments, playbook execution, evidence uploads, and simulated response actions.
- **Analytics**: Overview and trend API for live dashboards.
- **Demo Mode**: Seeded attack campaign API and optional background synthetic event generator.
- **Settings**: Analyst roster, system config, and demo runtime control APIs.
- **Database**: MySQL 8.4 schema with Alembic migration covering 11 core tables.
- **Frontend**: React 18 + TypeScript + Vite shell with 8 routed dashboard pages (Overview, Events, Alerts, MITRE ATT&CK, Cases, Rules, Analytics, Settings) and a custom dark visual design system.
- **Synthetic Mode**: Frontend-only toggle for dense, screenshot-ready portfolio views without backend mutation.
- **Reverse Proxy**: nginx routing `/api/*` to the backend and application routes to the frontend.
- **CI/CD**: GitHub Actions workflows for backend lint/test/security scan, frontend build verification, and CodeQL analysis.
- **DevEx**: Docker Compose dev override with hot reload, Makefile shortcuts, pre-commit hooks (Ruff, trailing whitespace, EOF fixer), and `.env.example`.
]]>
