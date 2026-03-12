// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useAlertStream } from "../../app/providers/AlertStreamProvider";
import { useDemoStore } from "../../app/store/demoStore";
import { useThemeStore } from "../../app/store/themeStore";
import { DataPanel } from "../../shared/components/DataPanel";
import { PageIntro } from "../../shared/components/PageIntro";
import { StatusBadge } from "../../shared/components/StatusBadge";
import type { DemoStatusResponse, SettingsStatusResponse } from "../../shared/types";
import { fetchJson, patchJson, postJson } from "../../shared/utils/api";
import { getLivePreviewRecommendation, getSyntheticAnalysts } from "../../shared/utils/mockData";

function toneForConnection(state: string) {
  if (state === "connected" || state === "synthetic") {
    return "connected";
  }
  if (state === "reconnecting" || state === "connecting") {
    return "medium";
  }
  return "offline";
}

export function SettingsPage() {
  const queryClient = useQueryClient();
  const theme = useThemeStore((state) => state.theme);
  const toggleTheme = useThemeStore((state) => state.toggleTheme);
  const {
    dataSource,
    intensity,
    liveStream,
    preferSyntheticForScreenshots,
    setDataSource,
    setIntensity,
    setLiveStream,
    setPreferSyntheticForScreenshots,
  } = useDemoStore();
  const { connectionState } = useAlertStream();

  const settingsQuery = useQuery({
    queryKey: ["settings-status"],
    queryFn: () => fetchJson<SettingsStatusResponse>("/settings/status"),
    enabled: dataSource === "live",
  });
  const demoStatusQuery = useQuery({
    queryKey: ["demo-status"],
    queryFn: () => fetchJson<DemoStatusResponse>("/demo/status"),
    enabled: dataSource === "live",
  });

  const updateDemoMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => patchJson("/settings/demo", payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["settings-status"] });
      await queryClient.invalidateQueries({ queryKey: ["demo-status"] });
      await queryClient.invalidateQueries({ queryKey: ["overview"] });
      await queryClient.invalidateQueries({ queryKey: ["analytics"] });
    },
  });

  const seedMutation = useMutation({
    mutationFn: () =>
      postJson("/demo/seed", {
        intensity,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["settings-status"] });
      await queryClient.invalidateQueries({ queryKey: ["demo-status"] });
      await queryClient.invalidateQueries({ queryKey: ["events"] });
      await queryClient.invalidateQueries({ queryKey: ["alerts"] });
      await queryClient.invalidateQueries({ queryKey: ["cases", "live"] });
      await queryClient.invalidateQueries({ queryKey: ["analytics"] });
      await queryClient.invalidateQueries({ queryKey: ["overview"] });
      await queryClient.invalidateQueries({ queryKey: ["mitre"] });
    },
  });

  const analysts =
    dataSource === "synthetic" ? getSyntheticAnalysts() : settingsQuery.data?.analysts ?? [];
  const liveDemo = settingsQuery.data?.demo ?? demoStatusQuery.data?.demo;
  const demoCounts = demoStatusQuery.data?.counts;

  return (
    <div className="page-grid">
      <PageIntro
        eyebrow="Settings"
        title="Platform controls"
        description="Switch between live APIs and the synthetic walkthrough, manage the backend demo pipeline, and keep the analyst roster visible for portfolio screenshots."
        actions={<StatusBadge label={`${dataSource} mode`} tone={dataSource === "synthetic" ? "connected" : "low"} />}
      />

      <div className="content-grid content-grid--wide">
        <DataPanel subtitle="Presentation and connectivity controls" title="Workspace preferences">
          <div className="settings-stack">
            <label className="setting-row">
              <div>
                <strong>Data source</strong>
                <p>{getLivePreviewRecommendation(dataSource)}</p>
              </div>
              <div className="segmented-control">
                <button
                  className={dataSource === "live" ? "segmented-control__option segmented-control__option--active" : "segmented-control__option"}
                  onClick={() => setDataSource("live")}
                  type="button"
                >
                  Live
                </button>
                <button
                  className={dataSource === "synthetic" ? "segmented-control__option segmented-control__option--active" : "segmented-control__option"}
                  onClick={() => setDataSource("synthetic")}
                  type="button"
                >
                  Synthetic
                </button>
              </div>
            </label>

            <label className="setting-row">
              <div>
                <strong>Synthetic intensity</strong>
                <p>Higher values increase chart volumes and queue density for screenshots.</p>
              </div>
              <div className="setting-slider">
                <input
                  max={10}
                  min={1}
                  onChange={(event) => setIntensity(Number(event.target.value))}
                  type="range"
                  value={intensity}
                />
                <span>{intensity}/10</span>
              </div>
            </label>

            <label className="setting-row">
              <div>
                <strong>Live WebSocket stream</strong>
                <p>Keep alert stream updates visible while browsing the queue.</p>
              </div>
              <button className="ghost-button ghost-button--compact" onClick={() => setLiveStream(!liveStream)} type="button">
                {liveStream ? "Disable" : "Enable"}
              </button>
            </label>

            <label className="setting-row">
              <div>
                <strong>Screenshot preference</strong>
                <p>Flag the synthetic walkthrough as the preferred showcase mode.</p>
              </div>
              <button
                className="ghost-button ghost-button--compact"
                onClick={() => setPreferSyntheticForScreenshots(!preferSyntheticForScreenshots)}
                type="button"
              >
                {preferSyntheticForScreenshots ? "Preferred" : "Not preferred"}
              </button>
            </label>

            <label className="setting-row">
              <div>
                <strong>Theme</strong>
                <p>Switch between the darker analyst shell and a lighter presentation theme.</p>
              </div>
              <button className="ghost-button ghost-button--compact" onClick={toggleTheme} type="button">
                {theme === "night" ? "Use dawn theme" : "Use night theme"}
              </button>
            </label>
          </div>
        </DataPanel>

        <DataPanel subtitle="Current platform state" title="Runtime status">
          <div className="watchlist-grid">
            <article className="watchlist-card">
              <span>Connection</span>
              <strong>{connectionState}</strong>
              <StatusBadge label={connectionState} tone={toneForConnection(connectionState)} />
            </article>
            <article className="watchlist-card">
              <span>Data source</span>
              <strong>{dataSource}</strong>
              <StatusBadge label={dataSource} tone={dataSource === "synthetic" ? "connected" : "neutral"} />
            </article>
            <article className="watchlist-card">
              <span>Theme</span>
              <strong>{theme}</strong>
              <StatusBadge label={theme} tone="neutral" />
            </article>
            <article className="watchlist-card">
              <span>Screenshot mode</span>
              <strong>{preferSyntheticForScreenshots ? "ready" : "manual"}</strong>
              <StatusBadge label={`L${intensity}`} tone="medium" />
            </article>
          </div>
        </DataPanel>
      </div>

      <div className="content-grid content-grid--wide">
        <DataPanel subtitle="Back the live dashboard with seeded telemetry and optional ongoing generation" title="Demo pipeline">
          <div className="settings-stack">
            <label className="setting-row">
              <div>
                <strong>Seed showcase dataset</strong>
                <p>Inject a realistic attack progression into the live event store for screenshots and demos.</p>
              </div>
              <button
                className="primary-button"
                disabled={seedMutation.isPending}
                onClick={() => seedMutation.mutate()}
                type="button"
              >
                {seedMutation.isPending ? "Seeding…" : "Seed live demo data"}
              </button>
            </label>

            <label className="setting-row">
              <div>
                <strong>Backend demo generator</strong>
                <p>Start or stop live synthetic ingestion while keeping the dashboard in API-backed mode.</p>
              </div>
              <button
                className="ghost-button ghost-button--compact"
                disabled={updateDemoMutation.isPending}
                onClick={() =>
                  updateDemoMutation.mutate({
                    enabled: !(liveDemo?.enabled ?? false),
                    intensity,
                  })
                }
                type="button"
              >
                {liveDemo?.enabled ? "Stop generator" : "Start generator"}
              </button>
            </label>

            <label className="setting-row">
              <div>
                <strong>Generator intensity</strong>
                <p>Push the current local intensity into the backend runtime without switching away from live mode.</p>
              </div>
              <button
                className="ghost-button ghost-button--compact"
                disabled={updateDemoMutation.isPending}
                onClick={() =>
                  updateDemoMutation.mutate({
                    intensity,
                    enabled: liveDemo?.enabled ?? false,
                  })
                }
                type="button"
              >
                Sync intensity
              </button>
            </label>
          </div>
        </DataPanel>

        <DataPanel subtitle="Live demo dataset state" title="Demo backend status">
          <div className="watchlist-grid">
            <article className="watchlist-card">
              <span>Generator</span>
              <strong>{liveDemo?.generator_status ?? "n/a"}</strong>
              <StatusBadge
                label={liveDemo?.enabled ? "enabled" : "disabled"}
                tone={liveDemo?.enabled ? "connected" : "neutral"}
              />
            </article>
            <article className="watchlist-card">
              <span>Seeded events</span>
              <strong>{demoCounts?.events ?? 0}</strong>
              <p>Persisted live demo telemetry</p>
            </article>
            <article className="watchlist-card">
              <span>Seeded alerts</span>
              <strong>{demoCounts?.alerts ?? 0}</strong>
              <p>Detections generated from demo events</p>
            </article>
            <article className="watchlist-card">
              <span>Demo cases</span>
              <strong>{demoCounts?.cases ?? 0}</strong>
              <p>{liveDemo?.seeded_at ? new Date(liveDemo.seeded_at).toLocaleString() : "Not seeded yet"}</p>
            </article>
          </div>
        </DataPanel>
      </div>

      <DataPanel subtitle={dataSource === "synthetic" ? "Synthetic analyst roster for screenshots" : "Analyst data from the live settings API"} title="Analyst management">
        <div className="watchlist-grid">
          {analysts.map((analyst) => (
            <article className="watchlist-card" key={analyst.username}>
              <span>{analyst.role}</span>
              <strong>{analyst.display_name}</strong>
              <p>{analyst.email}</p>
              <StatusBadge label={`${analyst.active_cases} active cases`} tone={analyst.active_cases ? "high" : "low"} />
            </article>
          ))}
        </div>
      </DataPanel>
    </div>
  );
}