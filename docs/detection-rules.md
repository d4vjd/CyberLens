# Detection Rules

CyberLens uses a Sigma-inspired YAML format for detection rules. Rules are stored in the `rules/` directory and synced into the database at backend startup.

## Rule Schema

```yaml
id: unique_rule_id              # Unique identifier (snake_case)
title: Human-Readable Title     # Display name
severity: low | medium | high | critical
type: threshold | pattern | sequence | aggregation

mitre:                          # MITRE ATT&CK mapping
  tactic: tactic-name           # e.g. credential-access
  technique_id: T1234.001       # Full technique/sub-technique ID
  technique_name: Technique     # Human-readable technique name

detection:
  filter:                       # Field-level match conditions
    event_type: <value>
    action: <value>
    source_ip: <value>
    dest_ip: <value>
    dest_port: <value>
    # Any normalised event field can be used

  # Type-specific configuration (see below)
  threshold: { ... }
  pattern: { ... }
  sequence: { ... }
  aggregation: { ... }

response:                       # Optional automated response
  playbook: playbook_id         # Links to playbooks/<id>.yml
  auto_actions: [action_name]   # Simulated response actions
```

## Rule Types

### Threshold

Fires when the number of matching events exceeds a count within a sliding time window, optionally grouped by a key field.

```yaml
detection:
  filter:
    event_type: authentication
    action: failed
    dest_port: 22
  threshold:
    count: 5
    group_by: source_ip
    timeframe: 300              # seconds
```

### Pattern

Fires when a single event matches all specified field conditions.

```yaml
detection:
  filter:
    event_type: process
    action: created
  pattern:
    field: command_line
    contains: "-EncodedCommand"
```

### Sequence

Fires when an ordered sequence of event patterns occurs within a time window.

```yaml
detection:
  filter:
    event_type: network
  sequence:
    steps:
      - { action: connect, dest_port: 445 }
      - { action: connect, dest_port: 135 }
    group_by: source_ip
    timeframe: 600
```

### Aggregation

Fires when an aggregate metric over a field exceeds a threshold within a window.

```yaml
detection:
  filter:
    event_type: network
    action: dns_query
  aggregation:
    metric: count
    field: dest_ip
    group_by: source_ip
    threshold: 100
    timeframe: 300
```

## Bundled Rules

CyberLens ships with 9 detection rules covering a range of ATT&CK techniques:

| Rule | Type | Severity | MITRE Technique |
|---|---|---|---|
| `brute_force_ssh` | threshold | high | T1110.001 — Password Guessing |
| `windows_logon_failures` | threshold | high | T1110.001 — Password Guessing |
| `port_scan_internal` | threshold | high | T1046 — Network Service Discovery |
| `lateral_movement_smb` | sequence | high | T1021.002 — SMB/Windows Admin Shares |
| `powershell_encoded_command` | pattern | critical | T1059.001 — PowerShell |
| `privilege_escalation_sudo` | pattern | high | T1548.003 — Sudo and Sudo Caching |
| `data_exfil_dns` | aggregation | critical | T1048.001 — Exfiltration Over DNS |
| `firewall_deny_spike` | threshold | medium | T1046 — Network Service Discovery |
| `vpn_impossible_travel` | aggregation | high | T1078 — Valid Accounts |

## Managing Rules

### Via API

- `GET /api/v1/rules` — List all rules.
- `POST /api/v1/rules` — Create a new rule (saves YAML to disk and reloads the catalog).
- `PATCH /api/v1/rules/{rule_id}` — Update a rule.
- `DELETE /api/v1/rules/{rule_id}` — Retire a rule and remove its YAML file.
- `POST /api/v1/rules/test` — Test a rule definition against recent historical events without persisting alerts.

### Via the Dashboard

The **Rules** page provides a visual editor for browsing, creating, and testing detection rules against historical telemetry.

<img src="assets/rules.png" alt="Rules Editor" width="100%" />

### MITRE ATT&CK Matrix

The **MITRE** page provides an interactive view of the MITRE ATT&CK matrix based on active detection rules and generated alerts.

<img src="assets/mitre.png" alt="MITRE ATT&CK Mapping" width="100%" />

### On Disk

Place `.yml` files in the `rules/` directory. The backend syncs all YAML rules into the database on startup. To trigger a mid-runtime reload:

```bash
curl -X POST http://localhost/api/v1/detection/rules/reload
```
]]>
