// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

export type Severity = "low" | "medium" | "high" | "critical";
export type AlertStatus =
  | "new"
  | "acknowledged"
  | "investigating"
  | "resolved"
  | "false_positive";
export type CaseStatus = "open" | "in_progress" | "escalated" | "resolved" | "closed";
export type RuleType = "threshold" | "pattern" | "sequence" | "aggregation";
export type DataSourceMode = "live" | "synthetic";
export type ConnectionState =
  | "offline"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "synthetic";

export type EventRecord = {
  id: number;
  timestamp: string;
  event_type: string;
  source_system: string;
  source_ip: string | null;
  dest_ip: string | null;
  source_port: number | null;
  dest_port: number | null;
  protocol: string | null;
  action: string | null;
  severity: Severity;
  hostname: string | null;
  username: string | null;
  message: string | null;
  raw_log: string;
  parsed_data: Record<string, unknown>;
  is_demo: boolean;
};

export type EventListResponse = {
  items: EventRecord[];
  total: number;
  offset: number;
  limit: number;
};

export type AlertRecord = {
  id: number;
  alert_uid: string;
  rule_id: number;
  title: string;
  severity: Severity;
  status: AlertStatus;
  source_ip: string | null;
  mitre_tactic: string | null;
  mitre_technique_id: string | null;
  matched_events: Array<Record<string, unknown>>;
  assigned_to: string | null;
  created_at: string;
};

export type AlertListResponse = {
  items: AlertRecord[];
  total: number;
  offset: number;
  limit: number;
};

export type MitreTechnique = {
  technique_id: string;
  name: string;
  tactic: string;
  description: string;
  rule_count: number;
  alert_count: number;
  last_alert_at: string | null;
};

export type MitreTacticColumn = {
  tactic: string;
  techniques: MitreTechnique[];
};

export type MitreMatrixResponse = {
  generated_at: string;
  tactics: MitreTacticColumn[];
};

export type MitreTechniqueDetail = {
  technique_id: string;
  name: string;
  tactic: string;
  description: string;
  rule_count: number;
  alert_count: number;
  last_alert_at: string | null;
  rule_ids: string[];
};

export type CaseTimelineEntry = {
  at: string;
  actor: string;
  kind: string;
  summary: string;
};

export type CaseRecord = {
  id: string;
  title: string;
  severity: Severity;
  status: CaseStatus;
  priority: number;
  assigned_to: string;
  playbook: string;
  sla_due_at: string;
  alerts: string[];
  evidence_count: number;
  summary: string;
  timeline: CaseTimelineEntry[];
};

export type RuleRecord = {
  id: string;
  title: string;
  description: string;
  severity: Severity;
  type: RuleType;
  enabled: boolean;
  mitre_tactic: string;
  mitre_technique_id: string;
  historical_matches: number;
  last_triggered_at: string | null;
  yaml: string;
};

export type OverviewMetric = {
  label: string;
  value: string;
  delta: string;
  tone: Severity | "neutral";
  tooltip?: string;
};

export type ThroughputPoint = {
  label: string;
  events: number;
  alerts: number;
};

export type DistributionPoint = {
  name: string;
  value: number;
  tone: Severity | "neutral";
};

export type SourceSummary = {
  label: string;
  count: number;
  context: string;
};

export type OverviewSnapshot = {
  metrics: OverviewMetric[];
  throughput: ThroughputPoint[];
  severityBreakdown: DistributionPoint[];
  topSources: SourceSummary[];
  watchlist: Array<{
    label: string;
    value: string;
    tone: Severity | "neutral";
    context: string;
  }>;
};

export type TrendPoint = {
  label: string;
  events: number;
  alerts: number;
};

export type GeoHotspot = {
  region: string;
  source_count: number;
  top_technique: string;
};

export type AttackerSummary = {
  source_ip: string;
  event_count: number;
  alert_count: number;
  technique: string;
};

export type AnalyticsMetricCard = {
  label: string;
  value: string;
  detail: string;
  tone: Severity | "neutral";
};

export type AnalyticsLane = {
  label: string;
  value: string;
  detail: string;
  tone: Severity | "neutral";
};

export type AnalyticsSnapshot = {
  metrics: AnalyticsMetricCard[];
  trend: TrendPoint[];
  severityBreakdown: DistributionPoint[];
  eventTypeMix: Array<{
    label: string;
    count: number;
    detail: string;
  }>;
  topAttackers: AttackerSummary[];
  baselineLanes: AnalyticsLane[];
};

export type AnalystRecord = {
  username: string;
  display_name: string;
  role: string;
  email: string;
  active_cases: number;
};

export type DemoSettings = {
  enabled: boolean;
  intensity: number;
  mode: string;
  seeded_at: string | null;
  generator_status: string;
};

export type SystemConfigItem = {
  key: string;
  value: Record<string, unknown>;
  description: string | null;
};

export type SettingsStatusResponse = {
  analysts: AnalystRecord[];
  demo: DemoSettings;
  configs: SystemConfigItem[];
};

export type DemoStatusResponse = {
  demo: DemoSettings;
  counts: {
    events: number;
    alerts: number;
    cases: number;
  };
};

export type DataClearResponse = {
  scope: string;
  cleared_events: number;
  cleared_alerts: number;
  cleared_cases: number;
  message: string;
};

export type BaselineEmitterStatus = {
  running: boolean;
  pipeline: string;
  emitted_batches: number;
  emitted_events: number;
  last_batch_size: number;
  last_emit_at: string | null;
  last_ingested_at: string | null;
  event_mix: Record<string, number>;
  parser_mix: Record<string, number>;
  last_checks: Record<string, string>;
  monitored_services: string[];
  last_error: string | null;
};

export type AnalyticsOverviewResponse = {
  metrics: Array<{ label: string; value: string; delta: string }>;
  trends: Array<{ bucket: string; events: number; alerts: number }>;
  top_sources: Array<{
    source_ip: string;
    event_count: number;
    alert_count: number;
    last_seen: string | null;
  }>;
};

export type CaseAlertSummary = {
  alert_uid: string;
  title: string;
  severity: Severity;
  status: AlertStatus;
};

export type CaseEventDetail = {
  id: number;
  event_type: string;
  actor: string;
  summary: string;
  details: Record<string, unknown>;
  created_at: string;
};

export type CaseEvidenceDetail = {
  id: number;
  filename: string;
  file_path: string;
  file_size: number;
  content_type: string;
  created_at: string;
};

export type ResponseActionDetail = {
  id: number;
  action_type: string;
  target: string;
  status: string;
  parameters: Record<string, unknown>;
  result: Record<string, unknown>;
  created_at: string;
};

export type CaseSummaryApi = {
  id: number;
  case_uid: string;
  title: string;
  severity: Severity;
  status: CaseStatus;
  priority: number;
  assigned_to: string | null;
  playbook_id: string | null;
  sla_due_at: string | null;
  alert_count: number;
  evidence_count: number;
  created_at: string;
};

export type CaseListResponseApi = {
  items: CaseSummaryApi[];
  total: number;
};

export type CaseDetailApi = {
  id: number;
  case_uid: string;
  title: string;
  description: string | null;
  severity: Severity;
  status: CaseStatus;
  priority: number;
  assigned_to: string | null;
  playbook_id: string | null;
  sla_due_at: string | null;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
  alerts: CaseAlertSummary[];
  timeline: CaseEventDetail[];
  evidence: CaseEvidenceDetail[];
  response_actions: ResponseActionDetail[];
};
