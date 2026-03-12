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
  CaseListResponseApi,
  DemoStatusResponse,
  EventListResponse,
  OverviewSnapshot,
  Severity,
} from "../../shared/types";
import { fetchJson } from "../../shared/utils/api";
import { getSyntheticOverview } from "../../shared/utils/mockData";

async function fetchLiveOverview(): Promise<OverviewSnapshot> {
  const [events, alerts, analytics, cases, demoStatus] = await Promise.all([
    fetchJson<EventListResponse>("/events?limit=100&offset=0"),
    fetchJson<AlertListResponse>("/alerts?limit=50&offset=0"),
    fetchJson<AnalyticsOverviewResponse>("/analytics/overview"),
    fetchJson<CaseListResponseApi>("/incidents"),
    fetchJson<DemoStatusResponse>("/demo/status"),
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

  return {
    metrics: [
      {
        label: "Events indexed",
        value: events.total.toLocaleString(),
        delta: `${demoStatus.counts.events.toLocaleString()} seeded demo events available`,
        tone: "low",
      },
      {
        label: "Open alerts",
        value: alerts.total.toString(),
        delta: `${alerts.items.filter((item) => item.status === "new").length} awaiting analyst action`,
        tone: alerts.items.some((item) => item.severity === "critical") ? "critical" : "medium",
      },
      {
        label: "Cases",
        value: cases.total.toString(),
        delta: `${demoStatus.counts.cases} seeded IR workflows ready`,
        tone: cases.total ? "high" : "neutral",
      },
      {
        label: "Streaming posture",
        value: demoStatus.demo.enabled ? "Generator active" : "Detection active",
        delta: demoStatus.demo.enabled ? `Intensity ${demoStatus.demo.intensity}/10` : "Live detection engine running",
        tone: demoStatus.demo.enabled ? "medium" : "low",
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
      context: item.alert_count ? `${item.alert_count} alerts linked` : "Telemetry only",
    })),
    watchlist: [
      { label: "ATT&CK coverage", value: "live matrix enabled", tone: "low" },
      {
        label: "IR workspace",
        value: cases.total ? `${cases.total} cases active` : "No live cases yet",
        tone: cases.total ? "medium" : "neutral",
      },
      {
        label: "Demo dataset",
        value: demoStatus.counts.events ? "seeded in live backend" : "seed from Settings",
        tone: demoStatus.counts.events ? "medium" : "neutral",
      },
      { label: "Alert stream", value: alerts.total ? "active" : "idle", tone: alerts.total ? "high" : "low" },
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

export function OverviewPage() {
  const dataSource = useDemoStore((state) => state.dataSource);
  const intensity = useDemoStore((state) => state.intensity);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["overview", dataSource, intensity],
    queryFn: () =>
      dataSource === "synthetic" ? Promise.resolve(getSyntheticOverview(intensity)) : fetchLiveOverview(),
  });

  return (
    <div className="page-grid">
      <PageIntro
        eyebrow="Situation Overview"
        title="SOC-wide telemetry pulse"
        description="A complete analyst-facing dashboard with live API mode for real backend data and a synthetic mode for screenshot-rich walkthroughs."
        actions={
          <StatusBadge
            label={dataSource === "synthetic" ? "Synthetic dataset enabled" : "Live API mode"}
            tone={dataSource === "synthetic" ? "connected" : "low"}
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
              value={metric.value}
            />
          ))}
        </div>
      </PageIntro>

      {isLoading ? <p className="table-message">Loading overview telemetry…</p> : null}
      {isError ? <p className="table-message">Failed to load overview data.</p> : null}

      {!isLoading && !isError && data ? (
        <>
          <div className="content-grid content-grid--wide">
            <DataPanel subtitle="Events and alert pressure by time bucket" title="Event rate">
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
                      contentStyle={{
                        background: "#18181b",
                        border: "1px solid rgba(255,255,255,0.1)",
                        borderRadius: 6,
                        fontSize: 12,
                      }}
                    />
                    <Area dataKey="events" fill="url(#eventsFill)" stroke="#3dd8c5" strokeWidth={2} />
                    <Area dataKey="alerts" fill="rgba(249,115,22,0.08)" stroke="#f97316" strokeWidth={1.5} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </DataPanel>

            <DataPanel subtitle="Weighted activity clusters" title="Top sources">
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
                      contentStyle={{
                        background: "#18181b",
                        border: "1px solid rgba(255,255,255,0.1)",
                        borderRadius: 6,
                        fontSize: 12,
                      }}
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

            <DataPanel subtitle="Operator watch list" title="Shift focus">
              <div className="watchlist-grid">
                {data.watchlist.map((item) => (
                  <article className="watchlist-card" key={item.label}>
                    <span>{item.label}</span>
                    <strong>{item.value}</strong>
                    <StatusBadge label={item.tone} tone={item.tone} />
                  </article>
                ))}
              </div>
            </DataPanel>
          </div>
        </>
      ) : null}
    </div>
  );
}