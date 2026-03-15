<![CDATA[# CyberLens Frontend

React + TypeScript dashboard for the CyberLens SIEM application.

## Overview

The frontend provides a professional SOC dashboard with 8 routed feature pages. It communicates with the backend API through nginx, prioritises live operational telemetry by default, and keeps synthetic/scenario tooling behind secondary controls.

## Feature Pages

| Page | Description |
|---|---|
| **Overview** | Live telemetry overview, baseline health, severity mix, and operational source visibility |
| **Events** | Paginated event browser with search and filters |
| **Alerts** | Alert listing with severity indicators |
| **MITRE ATT&CK** | Technique coverage matrix derived from live rules and alerts |
| **Cases** | Incident case management with details, comments, and actions |
| **Rules** | Detection rule browser and editor |
| **Analytics** | Operational trend analysis, severity distribution, event-type mix, and baseline pulse |
| **Settings** | Live controls, datastore clearing, analyst management, and hidden demo tooling |

## Module Layout

```
src/
├── app/            # App shell, routing, and layout
├── features/       # Feature modules (one directory per page)
│   ├── alerts/
│   ├── analytics/
│   ├── cases/
│   ├── events/
│   ├── mitre/
│   ├── overview/
│   ├── rules/
│   └── settings/
├── shared/         # Shared components, hooks, and API client
├── styles/         # Global CSS and design tokens
└── main.tsx        # Application entry point
```

## Running Locally (inside Docker)

The frontend is designed to run inside the Compose stack. See the [root README](../README.md) for startup instructions.

For development with HMR:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build frontend
```

The dev server is available at `http://localhost:5173`.

## Building

```bash
# Inside the container
npm run build

# Or via Make (also lint-checks the frontend)
make lint
```

## UI Notes

- Live mode is the primary experience and reads from backend APIs plus the baseline emitter.
- Synthetic mode is still available, but demo controls are intentionally de-emphasized in the Settings page.
- Theme switching is exposed as a compact header action instead of a persistent sidebar card.

## Key Dependencies

| Package | Purpose |
|---|---|
| React 18 | UI framework |
| TypeScript | Type safety |
| Vite | Dev server and build tool |
| React Router | Client-side routing |
| TanStack Query | Server state management and caching |
| Recharts | Chart and visualisation library |
| Zustand | Lightweight global state |
| clsx | Conditional CSS class utility |
]]>
