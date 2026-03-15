// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import { useQuery } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { useDemoStore } from "../../app/store/demoStore";
import { DataPanel } from "../../shared/components/DataPanel";
import { MetricCard } from "../../shared/components/MetricCard";
import { PageIntro } from "../../shared/components/PageIntro";
import { StatusBadge } from "../../shared/components/StatusBadge";
import type {
  AlertListResponse,
  AnalyticsOverviewResponse,
  BaselineEmitterStatus,
  CaseListResponseApi,
  DemoStatusResponse,
  EventListResponse,
  OverviewSnapshot,
  Severity,
} from "../../shared/types";
import { fetchJson } from "../../shared/utils/api";
import { formatCountLabel, humanizeIdentifier } from "../../shared/utils/format";
import { getSyntheticOverview } from "../../shared/utils/mockData";

async function fetchLiveOverview(): Promise<OverviewSnapshot> {
  const [events, alerts, analytics, cases, demoStatus, baselineStatus] = await Promise.all([
    fetchJson<EventListResponse>("/events?limit=100&offset=0"),
    fetchJson<AlertListResponse>("/alerts?limit=50&offset=0"),
    fetchJson<AnalyticsOverviewResponse>("/analytics/overview"),
    fetchJson<CaseListResponseApi>("/incidents"),
    fetchJson<DemoStatusResponse>("/demo/status"),
    fetchJson<BaselineEmitterStatus>("/ingest/baseline/status"),
  ]);

  const severityCounts = new Map<Severity, number>([
    ["critical", 0],
    ["high", 0],
    ["medium", 0],
    ["low", 0],
  ]);

  events.items.forEach((event) => {
    severityCounts.set(event.severity, (severityCounts.get(event.severity) ?? 0) + 1);
  });

  const healthChecks = baselineStatus.event_mix.service_health ?? 0;
  const heartbeats = baselineStatus.event_mix.service_heartbeat ?? 0;
  const networkFlows = baselineStatus.event_mix.network_flow ?? 0;
  const checkSummary = Object.entries(baselineStatus.last_checks)
    .map(([name, status]) => `${name}: ${status}`)
    .join(" · ");

  return {
    metrics: [
      {
        label: "Events indexed",
        value: events.total.toLocaleString(),
        delta: `${baselineStatus.emitted_events.toLocaleString()} operational baseline events emitted`,
        tone: "low",
        tooltip: "Total event records currently indexed in the backend event store.",
      },
      {
        label: "Open alerts",
        value: alerts.total.toString(),
        delta: `${alerts.items.filter((item) => item.status === "new").length} awaiting analyst action`,
        tone: alerts.items.some((item) => item.severity === "critical") ? "critical" : "medium",
        tooltip: "Alerts include queued detections that are still new, acknowledged, or actively under investigation.",
      },
      {
        label: "Cases",
        value: cases.total.toString(),
        delta: cases.total ? `${cases.total} investigations in motion` : "IR workspace is quiet",
        tone: cases.total ? "high" : "neutral",
        tooltip: "Case count reflects the incident workspace for live and seeded investigations.",
      },
      {
        label: "Baseline status",
        value: baselineStatus.running ? "Live telemetry active" : "Standby",
        delta: `${healthChecks} probes · ${heartbeats} heartbeats · ${networkFlows} flows`,
        tone: baselineStatus.running ? "low" : "neutral",
        tooltip: "Shows whether the live operational baseline is actively feeding the ingestion pipeline.",
      },
    ],
    throughput: analytics.trends.slice(-8).map((item) => ({
      label: item.bucket,
      events: item.events,
      alerts: item.alerts,
    })),
    severityBreakdown: [...severityCounts.entries()].map(([name, value]) => ({
      name: name[0].toUpperCase() + name.slice(1),
      value,
      tone: name,
    })),
    topSources: analytics.top_sources.slice(0, 5).map((item) => ({
      label: item.source_ip,
      count: item.event_count,
      context: item.alert_count
        ? `${item.alert_count} correlated alerts`
        : item.last_seen
          ? `Last seen ${new Date(item.last_seen).toLocaleString([], { timeStyle: "short" })}`
          : "Telemetry only",
    })),
    watchlist: [
      {
        label: "Health lane",
        value: `${healthChecks} probes`,
        tone: baselineStatus.last_error ? "high" : "low",
        context: baselineStatus.last_error
          ? baselineStatus.last_error
          : checkSummary || "Awaiting the first control-plane health probe.",
      },
      {
        label: "Heartbeat lane",
        value: `${heartbeats} signals`,
        tone: "low",
        context: `${baselineStatus.monitored_services.length} core services are sending routine heartbeats through the live syslog parser.`,
      },
      {
        label: "Network baseline",
        value: `${networkFlows} flows`,
        tone: "low",
        context: "Routine service-to-service activity is entering the live pipeline as normal netflow traffic.",
      },
      {
        label: "Scenario state",
        value: demoStatus.counts.events ? "Seeded" : "Empty",
        tone: demoStatus.counts.events ? "medium" : "neutral",
        context: demoStatus.counts.events
          ? "Demo scenarios remain available in Settings without driving the live baseline."
          : "Seed a scenario only when you need a denser walkthrough or IR storyline.",
      },
    ],
  };
}

const toneColors: Record<string, string> = {
  critical: "#ef4444",
  high: "#f97316",
  medium: "#eab308",
  low: "#22c55e",
  neutral: "#71717a",
};

const sharedTooltipStyle = {
  background: "#18181b",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 10,
  fontSize: 12,
  padding: "0.55rem 0.7rem",
};

function priorityLabel(tone: Severity | "neutral") {
  if (tone === "neutral") {
    return "Monitor";
  }
  return `${humanizeIdentifier(tone)} priority`;
}

export function OverviewPage() {
  const dataSource = useDemoStore((state) => state.dataSource);
  const intensity = useDemoStore((state) => state.intensity);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["overview", dataSource, intensity],
    queryFn: () =>
      dataSource === "synthetic" ? Promise.resolve(getSyntheticOverview(intensity)) : fetchLiveOverview(),
    refetchInterval: dataSource === "live" ? 8000 : false,
  });

  return (
    <div className="page-grid">
      <PageIntro
        eyebrow="Situation Overview"
        title={dataSource === "synthetic" ? "SOC-wide telemetry pulse" : "Live security operations"}
        description={
          dataSource === "synthetic"
            ? "A complete analyst-facing dashboard with live API mode for real backend data and a synthetic mode for screenshot-rich walkthroughs."
            : "Track live health probes, service heartbeats, and routine network activity through the same ingestion path used for real telemetry."
        }
        actions={
          <StatusBadge
            label={
              dataSource === "synthetic"
                ? `Intensity ${intensity}/10`
                : data?.metrics[3]?.value ?? "Live telemetry snapshot"
            }
            tone={dataSource === "synthetic" ? "connected" : "low"}
            tooltip={
              dataSource === "synthetic"
                ? "Synthetic density controls how aggressively overview charts, cases, and queues are populated."
                : "The overview is requesting live backend metrics, baseline status, and trend data."
            }
          />
        }
      >
        <div className="metric-grid">
          {data?.metrics.map((metric) => (
            <MetricCard
              delta={metric.delta}
              key={metric.label}
              label={metric.label}
              tone={metric.tone}
              tooltip={metric.tooltip}
              value={metric.value}
            />
          ))}
        </div>
      </PageIntro>

      {isLoading ? <div className="loading-state"><span className="loading-spinner" />Loading overview telemetry…</div> : null}
      {isError ? <div className="error-state">Failed to load overview data. Check your connection and try again.</div> : null}

      {!isLoading && !isError && data ? (
        <>
          <div className="content-grid content-grid--wide">
            <DataPanel
              subtitle="Events and alert pressure by time bucket"
              title={dataSource === "synthetic" ? "Event rate" : "Telemetry trend"}
            >
              <div className="chart-frame">
                <ResponsiveContainer height={300} width="100%">
                  <AreaChart data={data.throughput}>
                    <defs>
                      <linearGradient id="eventsFill" x1="0" x2="0" y1="0" y2="1">
                        <stop offset="0%" stopColor="#3dd8c5" stopOpacity={0.3} />
                        <stop offset="100%" stopColor="#3dd8c5" stopOpacity={0.02} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                    <XAxis dataKey="label" stroke="rgba(255,255,255,0.25)" tick={{ fontSize: 12 }} />
                    <YAxis stroke="rgba(255,255,255,0.25)" tick={{ fontSize: 12 }} />
                    <Tooltip
                      contentStyle={sharedTooltipStyle}
                      cursor={{ stroke: "rgba(255,255,255,0.16)", strokeDasharray: "4 4" }}
                      formatter={(value: number, name: string) => [
                        value.toLocaleString(),
                        name === "events" ? "Events" : "Alerts",
                      ]}
                      labelFormatter={(label) => `Bucket ${label}`}
                      itemStyle={{ color: "#e5e7eb" }}
                      labelStyle={{ color: "#e5e7eb", fontWeight: 600 }}
                    />
                    <Area dataKey="events" fill="url(#eventsFill)" stroke="#3dd8c5" strokeWidth={2} />
                    <Area dataKey="alerts" fill="rgba(249,115,22,0.08)" stroke="#f97316" strokeWidth={1.5} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </DataPanel>

            <DataPanel
              subtitle="Weighted activity clusters"
              title={dataSource === "synthetic" ? "Top sources" : "Busiest sources"}
            >
              <div className="list-panel">
                {data.topSources.map((source) => (
                  <article className="list-item" key={source.label}>
                    <div>
                      <strong>{source.label}</strong>
                      <p>{source.context}</p>
                    </div>
                    <span>{source.count.toLocaleString()}</span>
                  </article>
                ))}
              </div>
            </DataPanel>
          </div>

          <div className="content-grid">
            <DataPanel subtitle="Signal mix by severity" title="Severity distribution">
              <div className="chart-frame chart-frame--compact">
                <ResponsiveContainer height={260} width="100%">
                  <BarChart data={data.severityBreakdown}>
                    <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                    <XAxis dataKey="name" stroke="rgba(255,255,255,0.25)" tick={{ fontSize: 12 }} />
                    <YAxis stroke="rgba(255,255,255,0.25)" tick={{ fontSize: 12 }} />
                    <Tooltip
                      contentStyle={sharedTooltipStyle}
                      cursor={{ fill: "rgba(255,255,255,0.05)" }}
                      formatter={(value: number) => [value.toLocaleString(), "Signals"]}
                      itemStyle={{ color: "#e5e7eb" }}
                      labelStyle={{ color: "#e5e7eb", fontWeight: 600 }}
                    />
                    <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                      {data.severityBreakdown.map((entry) => (
                        <Cell fill={toneColors[entry.tone]} key={entry.name} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </DataPanel>

            <DataPanel
              subtitle={dataSource === "synthetic" ? "Operator watch list" : "Operator focus"}
              title={dataSource === "synthetic" ? "Shift focus" : "Live signals"}
            >
              <div className="watchlist-grid">
                {data.watchlist.map((item) => (
                  <article className="watchlist-card" key={item.label}>
                    <span>{item.label}</span>
                    <strong>{item.value}</strong>
                    <p>{item.context}</p>
                    <StatusBadge
                      label={priorityLabel(item.tone)}
                      tone={item.tone}
                      tooltip={`${item.label}: ${item.context}`}
                    />
                  </article>
                ))}
              </div>
            </DataPanel>
          </div>
          <DataPanel
            actions={
              <StatusBadge
                label={formatCountLabel(data.topSources.length, "source")}
                tone="neutral"
                tooltip="Top sources are weighted by signal volume and severity to keep the list stable."
              />
            }
            subtitle={
              dataSource === "synthetic"
                ? "Top-source narratives help anchor the charts to named activity clusters."
                : "The live summary keeps the busiest sources visible without dropping into the raw event stream."
            }
            title={dataSource === "synthetic" ? "Analyst notes" : "Live notes"}
          >
            <div className="timeline-preview">
              {data.topSources.slice(0, 3).map((source, index) => (
                <div className="timeline-preview__item" key={source.label}>
                  <span />
                  <div>
                    <strong>{`${index + 1}. ${source.label}`}</strong>
                    <p>{source.context}</p>
                  </div>
                </div>
              ))}
            </div>
          </DataPanel>
        </>
      ) : null}
    </div>
  );
}
