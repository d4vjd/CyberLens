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
  AnalyticsOverviewResponse,
  AnalyticsSnapshot,
  BaselineEmitterStatus,
  EventListResponse,
  Severity,
} from "../../shared/types";
import { fetchJson } from "../../shared/utils/api";
import { humanizeIdentifier } from "../../shared/utils/format";
import { getSyntheticAnalytics } from "../../shared/utils/mockData";

const chartTooltipStyle = {
  background: "#18181b",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 10,
  fontSize: 12,
  padding: "0.55rem 0.7rem",
};

const toneColors: Record<string, string> = {
  critical: "#ef4444",
  high: "#f97316",
  medium: "#eab308",
  low: "#22c55e",
  neutral: "#71717a",
};

function formatSourceLabel(value: string) {
  return value.includes("-") || value.includes("_") ? humanizeIdentifier(value) : value;
}

async function fetchLiveAnalytics(): Promise<AnalyticsSnapshot> {
  const [overview, events, baselineStatus] = await Promise.all([
    fetchJson<AnalyticsOverviewResponse>("/analytics/overview"),
    fetchJson<EventListResponse>("/events?limit=200&offset=0"),
    fetchJson<BaselineEmitterStatus>("/ingest/baseline/status"),
  ]);

  const severityCounts = new Map<Severity, number>([
    ["critical", 0],
    ["high", 0],
    ["medium", 0],
    ["low", 0],
  ]);
  const eventTypeCounts = new Map<string, number>();
  const distinctSources = new Set<string>();

  for (const event of events.items) {
    severityCounts.set(event.severity, (severityCounts.get(event.severity) ?? 0) + 1);
    eventTypeCounts.set(event.event_type, (eventTypeCounts.get(event.event_type) ?? 0) + 1);
    distinctSources.add(event.source_system || event.hostname || event.source_ip || "unknown");
  }

  const dominantSeverity =
    [...severityCounts.entries()].sort((left, right) => right[1] - left[1])[0]?.[0] ?? "low";
  const alertTotal = overview.top_sources.reduce((total, item) => total + item.alert_count, 0);
  const eventTotal = overview.top_sources.reduce((total, item) => total + item.event_count, 0);
  const eventTypeMix = [...eventTypeCounts.entries()]
    .sort((left, right) => right[1] - left[1])
    .slice(0, 5)
    .map(([label, count]) => ({
      label: humanizeIdentifier(label),
      count,
      detail: `${((count / Math.max(events.items.length, 1)) * 100).toFixed(0)}% of sampled events`,
    }));

  return {
    metrics: [
      {
        label: "Event throughput",
        value: eventTotal.toLocaleString(),
        detail: "Rolling activity in the current analytics window",
        tone: "low",
      },
      {
        label: "Alert conversion",
        value: `${alertTotal.toLocaleString()} alerts`,
        detail:
          eventTotal > 0
            ? `${((alertTotal / eventTotal) * 100).toFixed(1)}% of sampled source volume escalated`
            : "No alerts correlated in the current window",
        tone: alertTotal > 0 ? "medium" : "neutral",
      },
      {
        label: "Distinct sources",
        value: distinctSources.size.toString(),
        detail: "Hosts, services, and exporters contributing telemetry",
        tone: "neutral",
      },
      {
        label: "Dominant severity",
        value: humanizeIdentifier(dominantSeverity),
        detail: "Severity mix across the latest indexed events",
        tone: dominantSeverity,
      },
    ],
    trend: overview.trends.map((item) => ({
      label: item.bucket,
      events: item.events,
      alerts: item.alerts,
    })),
    severityBreakdown: [...severityCounts.entries()].map(([name, value]) => ({
      name: humanizeIdentifier(name),
      value,
      tone: name,
    })),
    eventTypeMix,
    topAttackers: overview.top_sources.map((item) => ({
      source_ip: item.source_ip,
      event_count: item.event_count,
      alert_count: item.alert_count,
      technique: item.last_seen
        ? `Last seen ${new Date(item.last_seen).toLocaleString()}`
        : "No recent timestamp available",
    })),
    baselineLanes: [
      {
        label: "Health baseline",
        value: `${baselineStatus.event_mix.service_health ?? 0} probes`,
        detail:
          Object.entries(baselineStatus.last_checks)
            .map(([name, status]) => `${name}: ${status}`)
            .join(" · ") || "Waiting for health checks to arrive",
        tone: baselineStatus.last_error ? "high" : "low",
      },
      {
        label: "Heartbeat baseline",
        value: `${baselineStatus.event_mix.service_heartbeat ?? 0} heartbeats`,
        detail: `${baselineStatus.monitored_services.length} monitored services are checking in routinely`,
        tone: "low",
      },
      {
        label: "Network baseline",
        value: `${baselineStatus.event_mix.network_flow ?? 0} flows`,
        detail: `${baselineStatus.last_batch_size ?? 0} events arrived in the latest live batch`,
        tone: "low",
      },
    ],
  };
}

export function AnalyticsPage() {
  const dataSource = useDemoStore((state) => state.dataSource);
  const intensity = useDemoStore((state) => state.intensity);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["analytics", dataSource, intensity],
    queryFn: () =>
      dataSource === "synthetic"
        ? Promise.resolve(getSyntheticAnalytics(intensity))
        : fetchLiveAnalytics(),
    refetchInterval: dataSource === "live" ? 8000 : false,
  });

  return (
    <div className="page-grid">
      <PageIntro
        eyebrow="Analytics"
        title={dataSource === "synthetic" ? "Synthetic campaign analytics" : "Operational analytics"}
        description={
          dataSource === "synthetic"
            ? "Review campaign pressure, severity distribution, and attack-path concentration across the synthetic dataset."
            : "Track signal quality, severity mix, and operational baselines without leaving the live telemetry path."
        }
        actions={
          <StatusBadge
            label={dataSource === "synthetic" ? "Synthetic analytics" : "Live analytics API"}
            tone={dataSource === "synthetic" ? "connected" : "low"}
          />
        }
      />

      {isLoading ? <div className="loading-state"><span className="loading-spinner" />Loading analytics…</div> : null}
      {isError ? <div className="error-state">Failed to build analytics snapshot.</div> : null}

      {!isLoading && !isError && data ? (
        <>
          <div className="metric-grid">
            {data.metrics.map((metric) => (
              <MetricCard
                delta={metric.detail}
                key={metric.label}
                label={metric.label}
                tone={metric.tone}
                value={metric.value}
              />
            ))}
          </div>

          <div className="content-grid content-grid--wide">
            <DataPanel
              subtitle="Event and alert activity over time"
              title={dataSource === "synthetic" ? "Campaign timeline" : "Operational trend"}
            >
              <div className="chart-frame">
                <ResponsiveContainer height={300} width="100%">
                  <AreaChart data={data.trend}>
                    <defs>
                      <linearGradient id="analyticsEvents" x1="0" x2="0" y1="0" y2="1">
                        <stop offset="0%" stopColor="#3dd8c5" stopOpacity={0.3} />
                        <stop offset="100%" stopColor="#3dd8c5" stopOpacity={0.02} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                    <XAxis dataKey="label" stroke="rgba(255,255,255,0.25)" tick={{ fontSize: 12 }} />
                    <YAxis stroke="rgba(255,255,255,0.25)" tick={{ fontSize: 12 }} />
                    <Tooltip
                      contentStyle={chartTooltipStyle}
                      cursor={{ stroke: "rgba(255,255,255,0.16)", strokeDasharray: "4 4" }}
                      formatter={(value: number, name: string) => [
                        value.toLocaleString(),
                        name === "events" ? "Events" : "Alerts",
                      ]}
                      itemStyle={{ color: "#e5e7eb" }}
                      labelStyle={{ color: "#e5e7eb", fontWeight: 600 }}
                    />
                    <Area dataKey="events" fill="url(#analyticsEvents)" stroke="#3dd8c5" strokeWidth={2} />
                    <Area dataKey="alerts" fill="rgba(249,115,22,0.08)" stroke="#f97316" strokeWidth={1.5} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </DataPanel>

            <DataPanel
              subtitle="Highest-volume entities in the current window"
              title={dataSource === "synthetic" ? "Top sources" : "Top signal sources"}
            >
              <div className="list-panel">
                {data.topAttackers.map((attacker) => (
                  <article className="list-item" key={attacker.source_ip}>
                    <div>
                      <strong>{formatSourceLabel(attacker.source_ip)}</strong>
                      <p>{attacker.technique}</p>
                    </div>
                    <span>
                      {attacker.event_count} evt / {attacker.alert_count} alrt
                    </span>
                  </article>
                ))}
              </div>
            </DataPanel>
          </div>

          <div className="content-grid">
            <DataPanel subtitle="Severity spread across the latest indexed sample" title="Severity distribution">
              <div className="chart-frame chart-frame--compact">
                <ResponsiveContainer height={240} width="100%">
                  <BarChart data={data.severityBreakdown}>
                    <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                    <XAxis dataKey="name" stroke="rgba(255,255,255,0.25)" tick={{ fontSize: 12 }} />
                    <YAxis stroke="rgba(255,255,255,0.25)" tick={{ fontSize: 12 }} />
                    <Tooltip
                      contentStyle={chartTooltipStyle}
                      cursor={{ fill: "rgba(255,255,255,0.04)" }}
                      formatter={(value: number) => [value.toLocaleString(), "Signals"]}
                      itemStyle={{ color: "#e5e7eb" }}
                      labelStyle={{ color: "#e5e7eb", fontWeight: 600 }}
                    />
                    <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                      {data.severityBreakdown.map((entry) => (
                        <Cell fill={toneColors[entry.tone]} key={entry.name} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </DataPanel>

            <DataPanel subtitle="Most common normalized activity types" title="Event type mix">
              <div className="list-panel">
                {data.eventTypeMix.map((entry) => (
                  <article className="list-item" key={entry.label}>
                    <div>
                      <strong>{entry.label}</strong>
                      <p>{entry.detail}</p>
                    </div>
                    <span>{entry.count}</span>
                  </article>
                ))}
              </div>
            </DataPanel>
          </div>

          <DataPanel subtitle="Baseline operational traffic entering the live pipeline" title="Baseline pulse">
            <div className="watchlist-grid">
              {data.baselineLanes.map((lane) => (
                <article className="watchlist-card" key={lane.label}>
                  <span>{lane.label}</span>
                  <strong>{lane.value}</strong>
                  <p>{lane.detail}</p>
                  <StatusBadge label={`${humanizeIdentifier(lane.tone)} priority`} tone={lane.tone} />
                </article>
              ))}
            </div>
          </DataPanel>
        </>
      ) : null}
    </div>
  );
}
