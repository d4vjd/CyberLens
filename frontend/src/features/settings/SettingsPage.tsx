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
import { humanizeIdentifier } from "../../shared/utils/format";
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
  const connectionLabel =
    dataSource === "live" && !liveStream ? "Paused" : humanizeIdentifier(connectionState);
  const connectionTone = dataSource === "live" && !liveStream ? "neutral" : toneForConnection(connectionState);

  return (
    <div className="page-grid">
      <PageIntro
        eyebrow="Settings"
        title="Platform controls"
        description="Switch between live telemetry and the synthetic walkthrough, manage the demo pipeline, and keep showcase settings clear for screenshots."
        actions={
          <StatusBadge
            label={dataSource === "synthetic" ? "Synthetic walkthrough" : "Live telemetry"}
            tone={dataSource === "synthetic" ? "connected" : "low"}
            tooltip={
              dataSource === "synthetic"
                ? "The workspace is currently using bundled showcase data."
                : "The workspace is currently sourcing data from live backend APIs."
            }
          />
        }
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
                  title="Use API-backed data from the running backend."
                  type="button"
                >
                  Live
                </button>
                <button
                  className={dataSource === "synthetic" ? "segmented-control__option segmented-control__option--active" : "segmented-control__option"}
                  onClick={() => setDataSource("synthetic")}
                  title="Use bundled showcase telemetry with denser charts and seeded investigations."
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
                <p>
                  {dataSource === "synthetic"
                    ? "Applies when you return to live telemetry. Synthetic mode bypasses the live alert stream."
                    : "Keep alert stream updates visible while browsing the queue."}
                </p>
              </div>
              <button
                className="ghost-button ghost-button--compact"
                disabled={dataSource === "synthetic"}
                onClick={() => setLiveStream(!liveStream)}
                title={
                  dataSource === "synthetic"
                    ? "Switch to live telemetry to manage the WebSocket alert stream."
                    : "Toggle the live alert stream without leaving the current page."
                }
                type="button"
              >
                {liveStream ? "Pause stream" : "Resume stream"}
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
                {preferSyntheticForScreenshots ? "Preferred" : "Manual"}
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
              <strong>{dataSource === "synthetic" ? "Bypassed" : connectionLabel}</strong>
              <StatusBadge
                label={dataSource === "synthetic" ? "Synthetic bypass" : connectionLabel}
                tone={connectionTone}
                tooltip="Current state of the live alert-stream bridge. Synthetic mode bypasses the live socket."
              />
            </article>
            <article className="watchlist-card">
              <span>Data source</span>
              <strong>{dataSource === "synthetic" ? "Synthetic walkthrough" : "Live APIs"}</strong>
              <StatusBadge
                label={dataSource === "synthetic" ? "Synthetic dataset" : "Live dataset"}
                tone={dataSource === "synthetic" ? "connected" : "neutral"}
                tooltip="Controls whether each page reads bundled demo data or backend API responses."
              />
            </article>
            <article className="watchlist-card">
              <span>Theme</span>
              <strong>{humanizeIdentifier(theme)}</strong>
              <StatusBadge
                label={`${humanizeIdentifier(theme)} theme`}
                tone="neutral"
                tooltip="Theme preference applies across the full shell, including charts, cards, and navigation."
              />
            </article>
            <article className="watchlist-card">
              <span>Screenshot preset</span>
              <strong>{preferSyntheticForScreenshots ? "Preferred" : "Manual"}</strong>
              <StatusBadge
                label={`Intensity ${intensity}/10`}
                tone="medium"
                tooltip="The current synthetic intensity used for screenshot and demo density."
              />
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
                title="Inject the bundled attack storyline into the live backend so events, alerts, cases, and ATT&CK coverage populate together."
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
                title="Toggle the backend demo generator without leaving live API mode."
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
                title="Push the current synthetic intensity value into the live backend generator configuration."
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
              <strong>{liveDemo?.generator_status ? humanizeIdentifier(liveDemo.generator_status) : "Not available"}</strong>
              <StatusBadge
                label={liveDemo?.enabled ? "enabled" : "disabled"}
                tone={liveDemo?.enabled ? "connected" : "neutral"}
                tooltip="Shows whether the live backend demo generator is actively producing new telemetry."
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
