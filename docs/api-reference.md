# API Reference

All endpoints are served under the `/api/v1` prefix via the nginx reverse proxy.

## Health

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health check |

---

## Ingestion

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/ingest/status` | Ingestion subsystem status |
| `POST` | `/ingest/raw` | Ingest a single raw log with optional metadata |
| `POST` | `/ingest/batch` | Ingest an array of logs (batched in chunks of up to 500) |

### Query Parameters for `GET /events`

| Parameter | Type | Description |
|---|---|---|
| `offset` | int | Pagination offset |
| `limit` | int | Page size |
| `event_type` | string | Filter by event type |
| `severity` | string | Filter by severity |
| `source_ip` | string | Filter by source IP |
| `dest_ip` | string | Filter by destination IP |
| `source_system` | string | Filter by source system |
| `action` | string | Filter by action |
| `search` | string | Full-text search across normalised fields |
| `start_time` | datetime | Start of time range filter |
| `end_time` | datetime | End of time range filter |

---

## Events

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/events` | Paginated event listing with search and filters |
| `GET` | `/events/{event_id}` | Single event detail |

---

## Detection & Rules

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/detection/status` | Detection engine status |
| `POST` | `/detection/rules/reload` | Reload rules from YAML into the active catalog |
| `GET` | `/rules` | List all detection rules |
| `POST` | `/rules` | Create a new rule (saves YAML to disk and reloads) |
| `PATCH` | `/rules/{rule_id}` | Update an existing rule |
| `DELETE` | `/rules/{rule_id}` | Retire a rule and remove its YAML file |
| `POST` | `/rules/test` | Test a rule against historical events without persisting alerts |

### Detection Notes

- Rules are loaded from `rules/*.yml` into the database at startup.
- `POST /rules` and `PATCH /rules/{rule_id}` save the YAML back to disk and reload the active catalog.
- `POST /rules/test` evaluates a YAML rule body against recent events and returns matches without side effects.
- Alerts are generated asynchronously from the Redis event stream using threshold, pattern, sequence, and aggregation evaluators.
- Generated alerts are published to `cyberlens:alerts` for WebSocket fan-out.

---

## Alerts

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/alerts` | Paginated alert listing |
| `GET` | `/alerts/{alert_id}` | Single alert detail |

---

## MITRE ATT&CK

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/mitre/status` | MITRE subsystem status |
| `GET` | `/mitre/matrix` | Full ATT&CK matrix with coverage from live rules and alerts |
| `GET` | `/mitre/techniques/{technique_id}` | Detail for a specific technique |

---

## Incident Response

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/incidents/status` | Incident subsystem status |
| `GET` | `/incidents` | List all cases |
| `POST` | `/incidents` | Create a new case |
| `GET` | `/incidents/{case_uid}` | Case detail with comments, evidence, and actions |
| `PATCH` | `/incidents/{case_uid}` | Update case metadata (status, severity, assignee) |
| `POST` | `/incidents/from-alerts/{alert_id}` | Escalate an alert into a new case |
| `POST` | `/incidents/{case_uid}/comments` | Add a comment to a case |
| `POST` | `/incidents/{case_uid}/playbook/run` | Execute a playbook against a case |
| `GET` | `/incidents/{case_uid}/response-actions` | List response actions for a case |
| `POST` | `/incidents/{case_uid}/response-actions` | Execute a simulated response action |
| `POST` | `/incidents/{case_uid}/evidence` | Upload evidence to a case |

### Incident Response Notes

- Cases can be created directly or escalated from alerts.
- Playbooks are loaded from `playbooks/*.yml` and trigger simulated response actions.
- Evidence uploads are stored on the backend filesystem and tracked in case detail responses.

---

## Analytics

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/analytics/status` | Analytics subsystem status |
| `GET` | `/analytics/overview` | Aggregated trends, top sources, and alert breakdowns |

---

## Demo

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/demo/status` | Seeded counts for events, alerts, and cases |
| `POST` | `/demo/seed` | Seed a realistic attack campaign into the live datastore |
| `POST` | `/demo/generator/start` | Start the background synthetic event generator |
| `POST` | `/demo/generator/stop` | Stop the background generator |

### Seed Request Body

```json
{
  "intensity": 6
}
```

`intensity` controls the density of generated events and alerts (1–10 scale).

---

## Settings

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/settings/status` | Settings subsystem status |
| `GET` | `/settings/analysts` | List SOC analysts |
| `GET` | `/settings/demo` | Current demo runtime configuration |
| `PATCH` | `/settings/demo` | Update demo settings (toggle generator, etc.) |
| `GET` | `/settings/config` | System configuration |
]]>
