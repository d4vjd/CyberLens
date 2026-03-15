// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import type {
  AlertListResponse,
  AlertRecord,
  AnalyticsSnapshot,
  AnalystRecord,
  CaseRecord,
  DataSourceMode,
  EventListResponse,
  EventRecord,
  MitreMatrixResponse,
  MitreTechniqueDetail,
  OverviewSnapshot,
  RuleRecord,
  Severity,
} from "../types";

type EventFilters = {
  search?: string;
  eventType?: string;
  sourceSystem?: string;
  severity?: string;
  offset?: number;
  limit?: number;
};

type AlertFilters = {
  search?: string;
  severity?: string;
  status?: string;
};

const syntheticEvents: EventRecord[] = [
  {
    id: 1001,
    timestamp: "2026-03-12T09:10:01Z",
    event_type: "authentication",
    source_system: "syslog",
    source_ip: "198.51.100.42",
    dest_ip: "10.20.3.12",
    source_port: 51101,
    dest_port: 22,
    protocol: "tcp",
    action: "failed",
    severity: "high",
    hostname: "bastion-edge-01",
    username: "admin",
    message: "Failed password for invalid user admin from 198.51.100.42 port 51101 ssh2",
    raw_log:
      "<34>Mar 12 09:10:01 bastion-edge-01 sshd[2234]: Failed password for invalid user admin from 198.51.100.42 port 51101 ssh2",
    parsed_data: { scenario: "brute_force", phase: 1 },
    is_demo: true,
  },
  {
    id: 1002,
    timestamp: "2026-03-12T09:10:13Z",
    event_type: "authentication",
    source_system: "syslog",
    source_ip: "198.51.100.42",
    dest_ip: "10.20.3.12",
    source_port: 51102,
    dest_port: 22,
    protocol: "tcp",
    action: "failed",
    severity: "high",
    hostname: "bastion-edge-01",
    username: "admin",
    message: "Failed password for invalid user admin from 198.51.100.42 port 51102 ssh2",
    raw_log:
      "<34>Mar 12 09:10:13 bastion-edge-01 sshd[2235]: Failed password for invalid user admin from 198.51.100.42 port 51102 ssh2",
    parsed_data: { scenario: "brute_force", phase: 1 },
    is_demo: true,
  },
  {
    id: 1003,
    timestamp: "2026-03-12T09:10:25Z",
    event_type: "authentication",
    source_system: "syslog",
    source_ip: "198.51.100.42",
    dest_ip: "10.20.3.12",
    source_port: 51103,
    dest_port: 22,
    protocol: "tcp",
    action: "failed",
    severity: "high",
    hostname: "bastion-edge-01",
    username: "admin",
    message: "Failed password for invalid user admin from 198.51.100.42 port 51103 ssh2",
    raw_log:
      "<34>Mar 12 09:10:25 bastion-edge-01 sshd[2236]: Failed password for invalid user admin from 198.51.100.42 port 51103 ssh2",
    parsed_data: { scenario: "brute_force", phase: 1 },
    is_demo: true,
  },
  {
    id: 1004,
    timestamp: "2026-03-12T09:10:37Z",
    event_type: "authentication",
    source_system: "syslog",
    source_ip: "198.51.100.42",
    dest_ip: "10.20.3.12",
    source_port: 51104,
    dest_port: 22,
    protocol: "tcp",
    action: "failed",
    severity: "high",
    hostname: "bastion-edge-01",
    username: "admin",
    message: "Failed password for invalid user admin from 198.51.100.42 port 51104 ssh2",
    raw_log:
      "<34>Mar 12 09:10:37 bastion-edge-01 sshd[2237]: Failed password for invalid user admin from 198.51.100.42 port 51104 ssh2",
    parsed_data: { scenario: "brute_force", phase: 1 },
    is_demo: true,
  },
  {
    id: 1005,
    timestamp: "2026-03-12T09:10:49Z",
    event_type: "authentication",
    source_system: "syslog",
    source_ip: "198.51.100.42",
    dest_ip: "10.20.3.12",
    source_port: 51105,
    dest_port: 22,
    protocol: "tcp",
    action: "failed",
    severity: "critical",
    hostname: "bastion-edge-01",
    username: "admin",
    message: "Failed password for invalid user admin from 198.51.100.42 port 51105 ssh2",
    raw_log:
      "<34>Mar 12 09:10:49 bastion-edge-01 sshd[2238]: Failed password for invalid user admin from 198.51.100.42 port 51105 ssh2",
    parsed_data: { scenario: "brute_force", phase: 1 },
    is_demo: true,
  },
  {
    id: 1006,
    timestamp: "2026-03-12T09:24:12Z",
    event_type: "network_scan",
    source_system: "netflow",
    source_ip: "203.0.113.17",
    dest_ip: "10.20.1.44",
    source_port: 40211,
    dest_port: 443,
    protocol: "tcp",
    action: "allowed",
    severity: "medium",
    hostname: "web-prod-01",
    username: null,
    message: "Rapid connection attempts across adjacent service ports",
    raw_log: "SRC=203.0.113.17 DST=10.20.1.44 PROTO=TCP DPT=443 FLAGS=SYN SCAN=horizontal",
    parsed_data: { scenario: "port_scan", phase: 0 },
    is_demo: true,
  },
  {
    id: 1007,
    timestamp: "2026-03-12T09:24:15Z",
    event_type: "network_scan",
    source_system: "netflow",
    source_ip: "203.0.113.17",
    dest_ip: "10.20.1.45",
    source_port: 40212,
    dest_port: 445,
    protocol: "tcp",
    action: "allowed",
    severity: "medium",
    hostname: "file-prod-02",
    username: null,
    message: "Rapid connection attempts across adjacent service ports",
    raw_log: "SRC=203.0.113.17 DST=10.20.1.45 PROTO=TCP DPT=445 FLAGS=SYN SCAN=horizontal",
    parsed_data: { scenario: "port_scan", phase: 0 },
    is_demo: true,
  },
  {
    id: 1008,
    timestamp: "2026-03-12T09:24:18Z",
    event_type: "network_scan",
    source_system: "netflow",
    source_ip: "203.0.113.17",
    dest_ip: "10.20.1.46",
    source_port: 40213,
    dest_port: 3389,
    protocol: "tcp",
    action: "allowed",
    severity: "medium",
    hostname: "rdp-jump-01",
    username: null,
    message: "Rapid connection attempts across adjacent service ports",
    raw_log: "SRC=203.0.113.17 DST=10.20.1.46 PROTO=TCP DPT=3389 FLAGS=SYN SCAN=horizontal",
    parsed_data: { scenario: "port_scan", phase: 0 },
    is_demo: true,
  },
  {
    id: 1009,
    timestamp: "2026-03-12T10:01:42Z",
    event_type: "process_creation",
    source_system: "windows_event",
    source_ip: "10.20.4.88",
    dest_ip: null,
    source_port: null,
    dest_port: null,
    protocol: null,
    action: "executed",
    severity: "high",
    hostname: "wks-finance-14",
    username: "fhernandez",
    message: "powershell.exe launched with encoded command",
    raw_log:
      "{\"EventID\":4688,\"Computer\":\"wks-finance-14\",\"CommandLine\":\"powershell.exe -enc SQBFAFgA...\"}",
    parsed_data: { scenario: "powershell", phase: 2 },
    is_demo: true,
  },
  {
    id: 1010,
    timestamp: "2026-03-12T10:02:10Z",
    event_type: "process_creation",
    source_system: "windows_event",
    source_ip: "10.20.4.88",
    dest_ip: null,
    source_port: null,
    dest_port: null,
    protocol: null,
    action: "executed",
    severity: "critical",
    hostname: "wks-finance-14",
    username: "fhernandez",
    message: "powershell.exe contacted staging host after encoded command",
    raw_log:
      "{\"EventID\":4688,\"Computer\":\"wks-finance-14\",\"Parent\":\"winword.exe\",\"CommandLine\":\"powershell.exe -enc SQBFAFgA...\"}",
    parsed_data: { scenario: "powershell", phase: 2 },
    is_demo: true,
  },
  {
    id: 1011,
    timestamp: "2026-03-12T10:02:42Z",
    event_type: "dns_request",
    source_system: "firewall",
    source_ip: "10.20.4.88",
    dest_ip: "203.0.113.91",
    source_port: 54601,
    dest_port: 53,
    protocol: "udp",
    action: "allowed",
    severity: "medium",
    hostname: "wks-finance-14",
    username: "fhernandez",
    message: "Resolved staging domain tied to current phishing case",
    raw_log:
      "{\"src_ip\":\"10.20.4.88\",\"dest_ip\":\"203.0.113.91\",\"query\":\"cdn-auth-sync.example\",\"action\":\"allowed\"}",
    parsed_data: { scenario: "powershell", phase: 2 },
    is_demo: true,
  },
  {
    id: 1012,
    timestamp: "2026-03-12T10:30:08Z",
    event_type: "authentication",
    source_system: "windows_event",
    source_ip: "10.20.4.88",
    dest_ip: "10.20.5.14",
    source_port: null,
    dest_port: 445,
    protocol: "tcp",
    action: "success",
    severity: "high",
    hostname: "srv-hr-02",
    username: "svc-backup",
    message: "Successful network logon using service account",
    raw_log: "{\"EventID\":4624,\"Computer\":\"srv-hr-02\",\"LogonType\":3,\"TargetUserName\":\"svc-backup\"}",
    parsed_data: { scenario: "lateral_movement", phase: 3 },
    is_demo: true,
  },
  {
    id: 1013,
    timestamp: "2026-03-12T10:30:19Z",
    event_type: "file_share_access",
    source_system: "windows_event",
    source_ip: "10.20.4.88",
    dest_ip: "10.20.5.14",
    source_port: null,
    dest_port: 445,
    protocol: "tcp",
    action: "opened",
    severity: "critical",
    hostname: "srv-hr-02",
    username: "svc-backup",
    message: "Administrative share accessed from compromised workstation",
    raw_log: "{\"EventID\":5140,\"ShareName\":\"\\\\*\\\\ADMIN$\",\"IpAddress\":\"10.20.4.88\"}",
    parsed_data: { scenario: "lateral_movement", phase: 3 },
    is_demo: true,
  },
  {
    id: 1014,
    timestamp: "2026-03-12T11:04:51Z",
    event_type: "privilege_change",
    source_system: "syslog",
    source_ip: "10.20.5.14",
    dest_ip: null,
    source_port: null,
    dest_port: null,
    protocol: null,
    action: "sudo",
    severity: "critical",
    hostname: "linux-batch-03",
    username: "svc-backup",
    message: "svc-backup invoked sudo to spawn interactive shell",
    raw_log: "sudo: svc-backup : TTY=pts/2 ; PWD=/tmp ; USER=root ; COMMAND=/bin/bash",
    parsed_data: { scenario: "privilege_escalation", phase: 4 },
    is_demo: true,
  },
  {
    id: 1015,
    timestamp: "2026-03-12T11:33:08Z",
    event_type: "data_transfer",
    source_system: "firewall",
    source_ip: "10.20.5.14",
    dest_ip: "192.0.2.88",
    source_port: 54011,
    dest_port: 21,
    protocol: "tcp",
    action: "allowed",
    severity: "critical",
    hostname: "linux-batch-03",
    username: "svc-backup",
    message: "Bulk outbound transfer over FTP after archive creation",
    raw_log:
      "{\"src_ip\":\"10.20.5.14\",\"dest_ip\":\"192.0.2.88\",\"protocol\":\"ftp\",\"bytes_out\":58222118}",
    parsed_data: { scenario: "data_exfiltration", phase: 5 },
    is_demo: true,
  },
  {
    id: 1016,
    timestamp: "2026-03-12T11:33:25Z",
    event_type: "data_transfer",
    source_system: "firewall",
    source_ip: "10.20.5.14",
    dest_ip: "192.0.2.88",
    source_port: 54012,
    dest_port: 21,
    protocol: "tcp",
    action: "allowed",
    severity: "critical",
    hostname: "linux-batch-03",
    username: "svc-backup",
    message: "Second outbound FTP transfer exceeded baseline threshold",
    raw_log:
      "{\"src_ip\":\"10.20.5.14\",\"dest_ip\":\"192.0.2.88\",\"protocol\":\"ftp\",\"bytes_out\":73110429}",
    parsed_data: { scenario: "data_exfiltration", phase: 5 },
    is_demo: true,
  },
  {
    id: 1017,
    timestamp: "2026-03-12T12:11:03Z",
    event_type: "vpn_login",
    source_system: "json_generic",
    source_ip: "203.0.113.201",
    dest_ip: null,
    source_port: null,
    dest_port: null,
    protocol: null,
    action: "success",
    severity: "medium",
    hostname: "vpn-edge-01",
    username: "snguyen",
    message: "VPN login accepted from Amsterdam",
    raw_log:
      "{\"event\":\"vpn_login\",\"username\":\"snguyen\",\"country\":\"NL\",\"source_ip\":\"203.0.113.201\"}",
    parsed_data: { scenario: "impossible_travel", country: "NL" },
    is_demo: true,
  },
  {
    id: 1018,
    timestamp: "2026-03-12T12:43:17Z",
    event_type: "vpn_login",
    source_system: "json_generic",
    source_ip: "198.51.100.170",
    dest_ip: null,
    source_port: null,
    dest_port: null,
    protocol: null,
    action: "success",
    severity: "medium",
    hostname: "vpn-edge-01",
    username: "snguyen",
    message: "VPN login accepted from Chicago 32 minutes after Amsterdam session",
    raw_log:
      "{\"event\":\"vpn_login\",\"username\":\"snguyen\",\"country\":\"US\",\"source_ip\":\"198.51.100.170\"}",
    parsed_data: { scenario: "impossible_travel", country: "US" },
    is_demo: true,
  },
];

const syntheticAlerts: AlertRecord[] = [
  {
    id: 1,
    alert_uid: "cl-alert-001",
    rule_id: 1,
    title: "SSH Brute Force Attempt",
    severity: "high",
    status: "new",
    source_ip: "198.51.100.42",
    mitre_tactic: "credential-access",
    mitre_technique_id: "T1110.001",
    matched_events: [{ id: 1005, hostname: "bastion-edge-01", count: 5 }],
    assigned_to: "mreyes",
    created_at: "2026-03-12T09:10:50Z",
  },
  {
    id: 2,
    alert_uid: "cl-alert-002",
    rule_id: 2,
    title: "Active Network Service Discovery",
    severity: "medium",
    status: "acknowledged",
    source_ip: "203.0.113.17",
    mitre_tactic: "reconnaissance",
    mitre_technique_id: "T1595",
    matched_events: [{ id: 1008, hosts: 3 }],
    assigned_to: "ahassan",
    created_at: "2026-03-12T09:24:19Z",
  },
  {
    id: 3,
    alert_uid: "cl-alert-003",
    rule_id: 3,
    title: "PowerShell Encoded Command",
    severity: "high",
    status: "investigating",
    source_ip: "10.20.4.88",
    mitre_tactic: "execution",
    mitre_technique_id: "T1059.001",
    matched_events: [{ id: 1010, user: "fhernandez" }],
    assigned_to: "ahassan",
    created_at: "2026-03-12T10:02:11Z",
  },
  {
    id: 4,
    alert_uid: "cl-alert-004",
    rule_id: 4,
    title: "SMB Lateral Movement Sequence",
    severity: "critical",
    status: "new",
    source_ip: "10.20.4.88",
    mitre_tactic: "lateral-movement",
    mitre_technique_id: "T1021.002",
    matched_events: [{ id: 1012 }, { id: 1013 }],
    assigned_to: null,
    created_at: "2026-03-12T10:30:21Z",
  },
  {
    id: 5,
    alert_uid: "cl-alert-005",
    rule_id: 5,
    title: "Privilege Escalation via sudo",
    severity: "critical",
    status: "resolved",
    source_ip: "10.20.5.14",
    mitre_tactic: "privilege-escalation",
    mitre_technique_id: "T1548",
    matched_events: [{ id: 1014 }],
    assigned_to: "mreyes",
    created_at: "2026-03-12T11:04:52Z",
  },
  {
    id: 6,
    alert_uid: "cl-alert-006",
    rule_id: 6,
    title: "Bulk Exfiltration Over FTP",
    severity: "critical",
    status: "investigating",
    source_ip: "10.20.5.14",
    mitre_tactic: "exfiltration",
    mitre_technique_id: "T1048.003",
    matched_events: [{ id: 1015 }, { id: 1016 }],
    assigned_to: "mreyes",
    created_at: "2026-03-12T11:33:26Z",
  },
  {
    id: 7,
    alert_uid: "cl-alert-007",
    rule_id: 7,
    title: "VPN Impossible Travel",
    severity: "medium",
    status: "false_positive",
    source_ip: "198.51.100.170",
    mitre_tactic: "credential-access",
    mitre_technique_id: "T1078",
    matched_events: [{ id: 1017 }, { id: 1018 }],
    assigned_to: "sclark",
    created_at: "2026-03-12T12:43:18Z",
  },
];

const syntheticCases: CaseRecord[] = [
  {
    id: "CL-2026-004",
    title: "Finance workstation compromise with staged lateral movement",
    severity: "critical",
    status: "in_progress",
    priority: 1,
    assigned_to: "Amira Hassan",
    playbook: "credential-compromise-containment",
    sla_due_at: "2026-03-12T17:00:00Z",
    alerts: ["cl-alert-003", "cl-alert-004"],
    evidence_count: 4,
    summary:
      "Encoded PowerShell execution on wks-finance-14 progressed to network logon and ADMIN$ access on srv-hr-02.",
    timeline: [
      {
        at: "2026-03-12T10:02:12Z",
        actor: "CyberLens",
        kind: "alert_linked",
        summary: "PowerShell execution alert linked to case.",
      },
      {
        at: "2026-03-12T10:31:02Z",
        actor: "Amira Hassan",
        kind: "assignment",
        summary: "Case claimed for triage and host scoping.",
      },
      {
        at: "2026-03-12T10:42:18Z",
        actor: "CyberLens",
        kind: "evidence_added",
        summary: "Attached encoded command line and SMB share access logs.",
      },
    ],
  },
  {
    id: "CL-2026-003",
    title: "Bulk FTP exfiltration from Linux batch tier",
    severity: "critical",
    status: "escalated",
    priority: 1,
    assigned_to: "Marcus Reyes",
    playbook: "data-exfiltration-response",
    sla_due_at: "2026-03-12T15:45:00Z",
    alerts: ["cl-alert-005", "cl-alert-006"],
    evidence_count: 6,
    summary:
      "Compromised service account escalated privileges and initiated repeated outbound FTP transfers to an external host.",
    timeline: [
      {
        at: "2026-03-12T11:04:53Z",
        actor: "CyberLens",
        kind: "alert_linked",
        summary: "Privilege escalation alert attached to exfiltration case.",
      },
      {
        at: "2026-03-12T11:34:14Z",
        actor: "Marcus Reyes",
        kind: "escalation",
        summary: "Escalated to infrastructure team for outbound block simulation.",
      },
      {
        at: "2026-03-12T11:38:42Z",
        actor: "CyberLens",
        kind: "playbook_step",
        summary: "Playbook requested account suspension and artifact collection.",
      },
    ],
  },
  {
    id: "CL-2026-001",
    title: "Repeated VPN geo anomalies for user snguyen",
    severity: "medium",
    status: "resolved",
    priority: 3,
    assigned_to: "Sophia Clark",
    playbook: "identity-anomaly-review",
    sla_due_at: "2026-03-15T12:43:00Z",
    alerts: ["cl-alert-007"],
    evidence_count: 2,
    summary:
      "Travel exception validated against executive itinerary. Alert dispositioned as expected behavior after analyst review.",
    timeline: [
      {
        at: "2026-03-12T12:43:18Z",
        actor: "CyberLens",
        kind: "alert_linked",
        summary: "Impossible travel alert added to case.",
      },
      {
        at: "2026-03-12T13:02:30Z",
        actor: "Sophia Clark",
        kind: "comment",
        summary: "Validated user itinerary with identity team.",
      },
      {
        at: "2026-03-12T13:05:01Z",
        actor: "Sophia Clark",
        kind: "status_change",
        summary: "Case closed as benign with supporting note.",
      },
    ],
  },
];

const syntheticRules: RuleRecord[] = [
  {
    id: "brute_force_ssh",
    title: "SSH Brute Force Attempt",
    description: "Threshold-based SSH authentication failure detection grouped by source IP.",
    severity: "high",
    type: "threshold",
    enabled: true,
    mitre_tactic: "credential-access",
    mitre_technique_id: "T1110.001",
    historical_matches: 14,
    last_triggered_at: "2026-03-12T09:10:50Z",
    yaml: `id: brute_force_ssh
title: SSH Brute Force Attempt
severity: high
type: threshold
mitre:
  tactic: credential-access
  technique_id: T1110.001
detection:
  filter:
    event_type: authentication
    action: failed
    dest_port: 22
  threshold:
    count: 5
    group_by: source_ip
    timeframe: 300`,
  },
  {
    id: "network_service_discovery",
    title: "Active Network Service Discovery",
    description: "Detects horizontal port sweeps over common administrative services.",
    severity: "medium",
    type: "aggregation",
    enabled: true,
    mitre_tactic: "reconnaissance",
    mitre_technique_id: "T1595",
    historical_matches: 9,
    last_triggered_at: "2026-03-12T09:24:19Z",
    yaml: `id: network_service_discovery
title: Active Network Service Discovery
severity: medium
type: aggregation
mitre:
  tactic: reconnaissance
  technique_id: T1595
detection:
  filter:
    event_type: network_scan
  aggregation:
    distinct_fields: [dest_ip, dest_port]
    threshold: 3
    group_by: source_ip
    timeframe: 120`,
  },
  {
    id: "powershell_encoded_command",
    title: "PowerShell Encoded Command",
    description: "Pattern rule for PowerShell launches containing encoded payloads.",
    severity: "high",
    type: "pattern",
    enabled: true,
    mitre_tactic: "execution",
    mitre_technique_id: "T1059.001",
    historical_matches: 6,
    last_triggered_at: "2026-03-12T10:02:11Z",
    yaml: `id: powershell_encoded_command
title: PowerShell Encoded Command
severity: high
type: pattern
mitre:
  tactic: execution
  technique_id: T1059.001
detection:
  filter:
    event_type: process_creation
  pattern:
    field: message
    contains:
      - encoded
      - PowerShell`,
  },
  {
    id: "smb_lateral_movement",
    title: "SMB Lateral Movement Sequence",
    description: "Sequence rule pairing service account logon with administrative share access.",
    severity: "critical",
    type: "sequence",
    enabled: true,
    mitre_tactic: "lateral-movement",
    mitre_technique_id: "T1021.002",
    historical_matches: 4,
    last_triggered_at: "2026-03-12T10:30:21Z",
    yaml: `id: smb_lateral_movement
title: SMB Lateral Movement Sequence
severity: critical
type: sequence
mitre:
  tactic: lateral-movement
  technique_id: T1021.002
detection:
  steps:
    - event_type: authentication
      action: success
    - event_type: file_share_access
      action: opened
  timeframe: 180`,
  },
  {
    id: "privilege_escalation_sudo",
    title: "Privilege Escalation via sudo",
    description: "Flags service-account sudo invocations spawning interactive shells.",
    severity: "critical",
    type: "pattern",
    enabled: true,
    mitre_tactic: "privilege-escalation",
    mitre_technique_id: "T1548",
    historical_matches: 3,
    last_triggered_at: "2026-03-12T11:04:52Z",
    yaml: `id: privilege_escalation_sudo
title: Privilege Escalation via sudo
severity: critical
type: pattern
mitre:
  tactic: privilege-escalation
  technique_id: T1548
detection:
  filter:
    event_type: privilege_change
  pattern:
    field: raw_log
    contains:
      - COMMAND=/bin/bash`,
  },
  {
    id: "ftp_data_exfiltration",
    title: "Bulk Exfiltration Over FTP",
    description: "Detects repeated large outbound FTP transfers to external hosts.",
    severity: "critical",
    type: "aggregation",
    enabled: true,
    mitre_tactic: "exfiltration",
    mitre_technique_id: "T1048.003",
    historical_matches: 5,
    last_triggered_at: "2026-03-12T11:33:26Z",
    yaml: `id: ftp_data_exfiltration
title: Bulk Exfiltration Over FTP
severity: critical
type: aggregation
mitre:
  tactic: exfiltration
  technique_id: T1048.003
detection:
  filter:
    event_type: data_transfer
    dest_port: 21
  aggregation:
    metric: sum_bytes
    threshold: 50000000
    group_by: source_ip
    timeframe: 300`,
  },
  {
    id: "vpn_impossible_travel",
    title: "VPN Impossible Travel",
    description: "Correlates geographically distant VPN logins within an infeasible window.",
    severity: "medium",
    type: "sequence",
    enabled: true,
    mitre_tactic: "credential-access",
    mitre_technique_id: "T1078",
    historical_matches: 7,
    last_triggered_at: "2026-03-12T12:43:18Z",
    yaml: `id: vpn_impossible_travel
title: VPN Impossible Travel
severity: medium
type: sequence
mitre:
  tactic: credential-access
  technique_id: T1078
detection:
  steps:
    - event_type: vpn_login
      action: success
    - event_type: vpn_login
      action: success
  timeframe: 3600`,
  },
  {
    id: "valid_accounts_admin",
    title: "Privileged Valid Accounts Usage",
    description: "Highlights use of sensitive service and administrative identities.",
    severity: "medium",
    type: "pattern",
    enabled: true,
    mitre_tactic: "credential-access",
    mitre_technique_id: "T1078",
    historical_matches: 11,
    last_triggered_at: "2026-03-12T10:30:08Z",
    yaml: `id: valid_accounts_admin
title: Privileged Valid Accounts Usage
severity: medium
type: pattern
mitre:
  tactic: credential-access
  technique_id: T1078
detection:
  filter:
    event_type: authentication
    action: success
  pattern:
    field: username
    contains:
      - svc-`,
  },
  {
    id: "password_spray_auth",
    title: "Password Guessing Baseline Drift",
    description: "Tracks distributed failed-password behavior against internet-facing logons.",
    severity: "high",
    type: "threshold",
    enabled: true,
    mitre_tactic: "credential-access",
    mitre_technique_id: "T1110",
    historical_matches: 8,
    last_triggered_at: "2026-03-11T22:08:10Z",
    yaml: `id: password_spray_auth
title: Password Guessing Baseline Drift
severity: high
type: threshold
mitre:
  tactic: credential-access
  technique_id: T1110
detection:
  filter:
    event_type: authentication
    action: failed
  threshold:
    count: 8
    group_by: username
    timeframe: 600`,
  },
];

const syntheticAnalysts: AnalystRecord[] = [
  {
    username: "ahassan",
    display_name: "Amira Hassan",
    role: "SOC Analyst II",
    email: "amira.hassan@cyberlens.local",
    active_cases: 1,
  },
  {
    username: "mreyes",
    display_name: "Marcus Reyes",
    role: "Incident Responder",
    email: "marcus.reyes@cyberlens.local",
    active_cases: 1,
  },
  {
    username: "sclark",
    display_name: "Sophia Clark",
    role: "Threat Hunter",
    email: "sophia.clark@cyberlens.local",
    active_cases: 0,
  },
];

function severityWeight(severity: Severity) {
  switch (severity) {
    case "critical":
      return 4;
    case "high":
      return 3;
    case "medium":
      return 2;
    default:
      return 1;
  }
}

function sortByNewest<T extends { timestamp?: string; created_at?: string }>(items: T[]) {
  return [...items].sort((left, right) => {
    const leftValue = new Date(left.timestamp ?? left.created_at ?? 0).getTime();
    const rightValue = new Date(right.timestamp ?? right.created_at ?? 0).getTime();
    return rightValue - leftValue;
  });
}

function filterBySearch(text: string | undefined, haystacks: Array<string | null | undefined>) {
  if (!text) {
    return true;
  }
  const needle = text.toLowerCase();
  return haystacks.some((value) => value?.toLowerCase().includes(needle));
}

function scaleValue(base: number, intensity: number) {
  const multiplier = 0.68 + intensity * 0.085;
  return Math.round(base * multiplier);
}

export function getSyntheticEvents(filters: EventFilters = {}): EventListResponse {
  const filtered = sortByNewest(syntheticEvents).filter((event) => {
    if (filters.eventType && event.event_type !== filters.eventType) {
      return false;
    }
    if (filters.sourceSystem && event.source_system !== filters.sourceSystem) {
      return false;
    }
    if (filters.severity && event.severity !== filters.severity) {
      return false;
    }
    return filterBySearch(filters.search, [
      event.message,
      event.hostname,
      event.username,
      event.raw_log,
      event.source_ip,
      event.dest_ip,
    ]);
  });

  const offset = filters.offset ?? 0;
  const limit = filters.limit ?? 25;
  return {
    items: filtered.slice(offset, offset + limit),
    total: filtered.length,
    offset,
    limit,
  };
}

export function getSyntheticAlerts(filters: AlertFilters = {}): AlertListResponse {
  const filtered = sortByNewest(syntheticAlerts).filter((alert) => {
    if (filters.severity && alert.severity !== filters.severity) {
      return false;
    }
    if (filters.status && alert.status !== filters.status) {
      return false;
    }
    return filterBySearch(filters.search, [
      alert.title,
      alert.source_ip,
      alert.mitre_tactic,
      alert.mitre_technique_id,
      alert.assigned_to,
    ]);
  });

  return {
    items: filtered,
    total: filtered.length,
    offset: 0,
    limit: filtered.length || 1,
  };
}

export function getSyntheticCases() {
  return [...syntheticCases];
}

export function getSyntheticRules() {
  return [...syntheticRules];
}

export function getSyntheticAnalysts() {
  return [...syntheticAnalysts];
}

export function getSyntheticMatrix(): MitreMatrixResponse {
  const grouped = new Map<string, MitreMatrixResponse["tactics"][number]["techniques"]>();

  syntheticRules.forEach((rule) => {
    const existing = grouped.get(rule.mitre_tactic) ?? [];
    const alertCount = syntheticAlerts.filter(
      (alert) => alert.mitre_technique_id === rule.mitre_technique_id,
    ).length;
    const previous = existing.find((technique) => technique.technique_id === rule.mitre_technique_id);

    if (previous) {
      previous.rule_count += 1;
      previous.alert_count = Math.max(previous.alert_count, alertCount);
      previous.last_alert_at =
        syntheticAlerts.find((alert) => alert.mitre_technique_id === rule.mitre_technique_id)
          ?.created_at ?? previous.last_alert_at;
    } else {
      existing.push({
        technique_id: rule.mitre_technique_id,
        name: techniqueName(rule.mitre_technique_id),
        tactic: rule.mitre_tactic,
        description: techniqueDescription(rule.mitre_technique_id),
        rule_count: 1,
        alert_count: alertCount,
        last_alert_at:
          syntheticAlerts.find((alert) => alert.mitre_technique_id === rule.mitre_technique_id)
            ?.created_at ?? null,
      });
    }

    grouped.set(rule.mitre_tactic, existing);
  });

  return {
    generated_at: new Date().toISOString(),
    tactics: [...grouped.entries()].map(([tactic, techniques]) => ({
      tactic,
      techniques: techniques.sort((left, right) =>
        left.technique_id.localeCompare(right.technique_id),
      ),
    })),
  };
}

export function getSyntheticTechniqueDetail(techniqueId: string): MitreTechniqueDetail | null {
  const relevantRules = syntheticRules.filter((rule) => rule.mitre_technique_id === techniqueId);
  if (!relevantRules.length) {
    return null;
  }

  const alerts = syntheticAlerts.filter((alert) => alert.mitre_technique_id === techniqueId);
  return {
    technique_id: techniqueId,
    name: techniqueName(techniqueId),
    tactic: relevantRules[0].mitre_tactic,
    description: techniqueDescription(techniqueId),
    rule_count: relevantRules.length,
    alert_count: alerts.length,
    last_alert_at: alerts[0]?.created_at ?? null,
    rule_ids: relevantRules.map((rule) => rule.id),
  };
}

export function getSyntheticOverview(intensity: number): OverviewSnapshot {
  const eventTotal = scaleValue(34821, intensity);
  const alertTotal = Math.max(1, scaleValue(18, intensity));
  const caseTotal = syntheticCases.filter((item) => item.status !== "closed").length;
  const mttdMinutes = Math.max(2, 8 - Math.floor(intensity / 2));
  const mttrMinutes = Math.max(18, 62 - intensity * 3);

  const baseThroughput = [
    { label: "00:00", events: 1210, alerts: 1 },
    { label: "04:00", events: 1640, alerts: 1 },
    { label: "08:00", events: 2830, alerts: 2 },
    { label: "10:00", events: 3950, alerts: 4 },
    { label: "12:00", events: 4410, alerts: 3 },
    { label: "14:00", events: 3680, alerts: 2 },
  ];

  const throughput = baseThroughput.map((point) => ({
    label: point.label,
    events: scaleValue(point.events, intensity),
    alerts: Math.max(1, scaleValue(point.alerts, intensity)),
  }));

  const severityBreakdown = [
    { name: "Critical", value: 6, tone: "critical" },
    { name: "High", value: 11, tone: "high" },
    { name: "Medium", value: 18, tone: "medium" },
    { name: "Low", value: 9, tone: "low" },
  ] as const;

  const sourceMap = new Map<string, { count: number; context: string }>();
  syntheticEvents.forEach((event) => {
    const label = event.source_ip ?? event.hostname ?? "unknown";
    const current = sourceMap.get(label) ?? { count: 0, context: event.event_type };
    current.count += severityWeight(event.severity);
    current.context = event.message ?? event.event_type;
    sourceMap.set(label, current);
  });

  const topSources = [...sourceMap.entries()]
    .map(([label, value]) => ({
      label,
      count: scaleValue(value.count * 42, intensity),
      context: value.context,
    }))
    .sort((left, right) => right.count - left.count)
    .slice(0, 5);

  return {
    metrics: [
      {
        label: "Events indexed",
        value: eventTotal.toLocaleString(),
        delta: `${intensity > 6 ? "+" : "-"}${Math.abs(intensity - 5) * 3 + 8}% vs baseline`,
        tone: "low",
        tooltip: "Synthetic event volume scales with the showcase intensity slider in Settings.",
      },
      {
        label: "Open alerts",
        value: alertTotal.toString(),
        delta: `${syntheticAlerts.filter((alert) => alert.status === "new").length} awaiting triage`,
        tone: "high",
        tooltip: "Alerts stay intentionally dense in synthetic mode so queue states remain screenshot-ready.",
      },
      {
        label: "Active cases",
        value: caseTotal.toString(),
        delta: `${syntheticCases.filter((item) => item.priority === 1).length} priority 1 investigations`,
        tone: "critical",
        tooltip: "Case totals reflect the seeded attack progression across identity, endpoint, and exfiltration workflows.",
      },
      {
        label: "MTTD / MTTR",
        value: `${mttdMinutes}m / ${mttrMinutes}m`,
        delta: "Synthetic benchmark profile",
        tone: "medium",
        tooltip: "Mean time to detect and mean time to respond are synthetic benchmarks for portfolio presentation, not live SLA measurements.",
      },
    ],
    throughput,
    severityBreakdown: severityBreakdown.map((item) => ({
      ...item,
      value: scaleValue(item.value, intensity),
    })),
    topSources,
    watchlist: [
      {
        label: "Credential misuse",
        value: "Elevated",
        tone: "high",
        context: "Repeated invalid logins are targeting bastion and VPN entry points.",
      },
      {
        label: "East-west movement",
        value: "Active",
        tone: "critical",
        context: "Administrative share access is chaining from the compromised workstation.",
      },
      {
        label: "Exfiltration volume",
        value: "Monitoring",
        tone: "medium",
        context: "Outbound transfer spikes remain below confirmed case-threshold volume.",
      },
      {
        label: "Demo readiness",
        value: "Ready",
        tone: "low",
        context: "Synthetic storylines are populated across events, alerts, cases, and ATT&CK coverage.",
      },
    ],
  };
}

export function getSyntheticAnalytics(intensity: number): AnalyticsSnapshot {
  const trend = [
    { label: "Mar 06", events: 4200, alerts: 4 },
    { label: "Mar 07", events: 4380, alerts: 5 },
    { label: "Mar 08", events: 4610, alerts: 6 },
    { label: "Mar 09", events: 5120, alerts: 7 },
    { label: "Mar 10", events: 5840, alerts: 8 },
    { label: "Mar 11", events: 6420, alerts: 10 },
    { label: "Mar 12", events: 7110, alerts: 13 },
  ].map((point) => ({
    label: point.label,
    events: scaleValue(point.events, intensity),
    alerts: Math.max(1, scaleValue(point.alerts, intensity)),
  }));

  const topAttackers = [
    {
      source_ip: "198.51.100.42",
      event_count: scaleValue(542, intensity),
      alert_count: 1,
      technique: "T1110.001",
    },
    {
      source_ip: "203.0.113.17",
      event_count: scaleValue(214, intensity),
      alert_count: 1,
      technique: "T1595",
    },
    {
      source_ip: "10.20.5.14",
      event_count: scaleValue(176, intensity),
      alert_count: 2,
      technique: "T1048.003",
    },
    {
      source_ip: "10.20.4.88",
      event_count: scaleValue(148, intensity),
      alert_count: 2,
      technique: "T1059.001",
    },
  ];

  return {
    metrics: [
      {
        label: "Event throughput",
        value: scaleValue(1436, intensity).toLocaleString(),
        detail: "Synthetic timeline volume across the current review window",
        tone: "medium",
      },
      {
        label: "Alert conversion",
        value: `${scaleValue(42, intensity)} detections`,
        detail: "Detection pressure synthesized from the scenario feed",
        tone: "high",
      },
      {
        label: "Distinct sources",
        value: scaleValue(19, intensity).toString(),
        detail: "Active entities contributing telemetry to the campaign",
        tone: "neutral",
      },
      {
        label: "Dominant severity",
        value: "High",
        detail: "Synthetic campaign tuned to keep escalation paths visible",
        tone: "high",
      },
    ],
    trend,
    severityBreakdown: [
      { name: "Critical", value: scaleValue(6, intensity), tone: "critical" },
      { name: "High", value: scaleValue(22, intensity), tone: "high" },
      { name: "Medium", value: scaleValue(15, intensity), tone: "medium" },
      { name: "Low", value: scaleValue(5, intensity), tone: "low" },
    ],
    eventTypeMix: [
      {
        label: "Authentication failures",
        count: scaleValue(24, intensity),
        detail: "Password-guessing and account access pressure",
      },
      {
        label: "Lateral movement",
        count: scaleValue(18, intensity),
        detail: "Remote execution and admin-share activity",
      },
      {
        label: "Privilege escalation",
        count: scaleValue(12, intensity),
        detail: "Elevation attempts requiring analyst review",
      },
      {
        label: "Exfiltration signals",
        count: scaleValue(8, intensity),
        detail: "Outbound transfer anomalies across monitored egress",
      },
    ],
    topAttackers,
    baselineLanes: [
      {
        label: "Detection lane",
        value: `${scaleValue(42, intensity)} alerts`,
        detail: "Synthetic detections remain elevated to support analyst walkthroughs",
        tone: "high",
      },
      {
        label: "Credential pressure",
        value: `${scaleValue(31, intensity)} auth events`,
        detail: "Repeated login pressure anchored to T1110.001 activity",
        tone: "high",
      },
      {
        label: "Operational noise",
        value: `${scaleValue(14, intensity)} routine events`,
        detail: "Background chatter preserves context around the attack chain",
        tone: "medium",
      },
    ],
  };
}

export function getLivePreviewRecommendation(mode: DataSourceMode) {
  if (mode === "synthetic") {
    return "Synthetic telemetry is enabled across every workflow so the product stays fully populated for demos and screenshots.";
  }

  return "Live APIs are active. Switch back to the synthetic walkthrough when you need denser showcase telemetry for screenshots.";
}

function techniqueName(techniqueId: string) {
  const names: Record<string, string> = {
    "T1110.001": "Password Guessing",
    T1595: "Active Scanning",
    "T1059.001": "PowerShell",
    "T1021.002": "SMB/Windows Admin Shares",
    T1548: "Abuse Elevation Control Mechanism",
    "T1048.003": "Exfiltration Over Unencrypted Non-C2 Protocol",
    T1078: "Valid Accounts",
    T1110: "Brute Force",
  };
  return names[techniqueId] ?? techniqueId;
}

function techniqueDescription(techniqueId: string) {
  const descriptions: Record<string, string> = {
    "T1110.001": "Adversaries may guess passwords against exposed authentication services.",
    T1595: "Adversaries may scan victim infrastructure to identify exposed services.",
    "T1059.001": "Adversaries may execute payloads through PowerShell on Windows hosts.",
    "T1021.002": "Adversaries may move laterally through SMB sessions and admin shares.",
    T1548: "Adversaries may elevate privileges through sudo or other elevation controls.",
    "T1048.003": "Adversaries may exfiltrate data over protocols not typically used for C2.",
    T1078: "Adversaries may use valid or stolen accounts to access target systems.",
    T1110: "Adversaries may brute force usernames or passwords at scale.",
  };
  return descriptions[techniqueId] ?? "ATT&CK technique details bundled for portfolio coverage.";
}
