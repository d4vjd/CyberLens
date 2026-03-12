<![CDATA[# CyberLens Frontend

React + TypeScript dashboard for the CyberLens SIEM application.

## Overview

The frontend provides a dark-themed SOC dashboard with 8 routed feature pages. It communicates with the backend API through nginx and supports a synthetic mode toggle for screenshot-ready portfolio views without backend dependency.

## Feature Pages

| Page | Description |
|---|---|
| **Overview** | Live event and alert trend charts, top sources |
| **Events** | Paginated event browser with search and filters |
| **Alerts** | Alert listing with severity indicators |
| **MITRE ATT&CK** | Technique coverage matrix derived from live rules and alerts |
| **Cases** | Incident case management with details, comments, and actions |
| **Rules** | Detection rule browser and editor |
| **Analytics** | Trend visualisations and source breakdowns |
| **Settings** | Analyst roster, system config, and demo controls |

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
