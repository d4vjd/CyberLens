// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import { useQuery } from "@tanstack/react-query";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { useDemoStore } from "../../app/store/demoStore";
import { DataPanel } from "../../shared/components/DataPanel";
import { PageIntro } from "../../shared/components/PageIntro";
import { StatusBadge } from "../../shared/components/StatusBadge";
import type { AnalyticsOverviewResponse, AnalyticsSnapshot } from "../../shared/types";
import { fetchJson } from "../../shared/utils/api";
import { getSyntheticAnalytics } from "../../shared/utils/mockData";

async function fetchLiveAnalytics(): Promise<AnalyticsSnapshot> {
  const overview = await fetchJson<AnalyticsOverviewResponse>("/analytics/overview");
  return {
    trend: overview.trends.map((item) => ({
      label: item.bucket,
      events: item.events,
      alerts: item.alerts,
    })),
    topAttackers: overview.top_sources.map((item) => ({
      source_ip: item.source_ip,
      event_count: item.event_count,
      alert_count: item.alert_count,
      technique: item.last_seen ? `Last seen ${new Date(item.last_seen).toLocaleString()}` : "No alert context yet",
    })),
    geoHotspots: overview.top_sources.slice(0, 6).map((item) => ({
      region: item.source_ip,
      source_count: item.event_count,
      top_technique: item.alert_count ? `${item.alert_count} alert(s) linked` : "Telemetry only",
    })),
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
  });

  return (
    <div className="page-grid">
      <PageIntro
        eyebrow="Analytics"
        title="Threat trend analysis"
        description="Chart event and alert drift, inspect noisy sources, and switch between the real backend snapshot and the denser synthetic campaign view."
        actions={
          <StatusBadge
            label={dataSource === "synthetic" ? "Synthetic campaign view" : "Live analytics API"}
            tone={dataSource === "synthetic" ? "connected" : "low"}
          />
        }
      />

      {isLoading ? <p className="table-message">Loading analytics…</p> : null}
      {isError ? <p className="table-message">Failed to build analytics snapshot.</p> : null}

      {!isLoading && !isError && data ? (
        <>
          <div className="content-grid content-grid--wide">
            <DataPanel subtitle="Event and alert trend over time" title="Trend analysis">
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
                      contentStyle={{
                        background: "#18181b",
                        border: "1px solid rgba(255,255,255,0.1)",
                        borderRadius: 6,
                        fontSize: 12,
                      }}
                    />
                    <Area dataKey="events" fill="url(#analyticsEvents)" stroke="#3dd8c5" strokeWidth={2} />
                    <Area dataKey="alerts" fill="rgba(249,115,22,0.08)" stroke="#f97316" strokeWidth={1.5} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </DataPanel>

            <DataPanel subtitle="Highest signal sources" title="Top attackers">
              <div className="list-panel">
                {data.topAttackers.map((attacker) => (
                  <article className="list-item" key={attacker.source_ip}>
                    <div>
                      <strong>{attacker.source_ip}</strong>
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

          <DataPanel subtitle="Geographic-style source clustering" title="Hotspots">
            <div className="watchlist-grid">
              {data.geoHotspots.map((hotspot) => (
                <article className="watchlist-card" key={hotspot.region}>
                  <span>{hotspot.region}</span>
                  <strong>{hotspot.source_count} sources</strong>
                  <p>{hotspot.top_technique}</p>
                </article>
              ))}
            </div>
          </DataPanel>
        </>
      ) : null}
    </div>
  );
}