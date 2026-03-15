// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useAlertStream } from "../../app/providers/AlertStreamProvider";
import { useDemoStore } from "../../app/store/demoStore";
import { useThemeStore } from "../../app/store/themeStore";
import { DataPanel } from "../../shared/components/DataPanel";
import { PageIntro } from "../../shared/components/PageIntro";
import { StatusBadge } from "../../shared/components/StatusBadge";
import type {
  BaselineEmitterStatus,
  DataClearResponse,
  DemoStatusResponse,
  SettingsStatusResponse,
} from "../../shared/types";
import { deleteJson, fetchJson, patchJson, postJson } from "../../shared/utils/api";
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
    refetchInterval: dataSource === "live" ? 8000 : false,
  });
  const demoStatusQuery = useQuery({
    queryKey: ["demo-status"],
    queryFn: () => fetchJson<DemoStatusResponse>("/demo/status"),
    enabled: dataSource === "live",
    refetchInterval: dataSource === "live" ? 8000 : false,
  });
  const baselineStatusQuery = useQuery({
    queryKey: ["baseline-status"],
    queryFn: () => fetchJson<BaselineEmitterStatus>("/ingest/baseline/status"),
    enabled: dataSource === "live",
    refetchInterval: dataSource === "live" ? 5000 : false,
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

  const clearSeededMutation = useMutation({
    mutationFn: () => deleteJson<DataClearResponse>("/demo/seeded-data"),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["settings-status"] });
      await queryClient.invalidateQueries({ queryKey: ["demo-status"] });
      await queryClient.invalidateQueries({ queryKey: ["baseline-status"] });
      await queryClient.invalidateQueries({ queryKey: ["events"] });
      await queryClient.invalidateQueries({ queryKey: ["alerts"] });
      await queryClient.invalidateQueries({ queryKey: ["cases", "live"] });
      await queryClient.invalidateQueries({ queryKey: ["analytics"] });
      await queryClient.invalidateQueries({ queryKey: ["overview"] });
      await queryClient.invalidateQueries({ queryKey: ["mitre"] });
    },
  });

  const clearLiveMutation = useMutation({
    mutationFn: () => deleteJson<DataClearResponse>("/demo/live-data"),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["settings-status"] });
      await queryClient.invalidateQueries({ queryKey: ["demo-status"] });
      await queryClient.invalidateQueries({ queryKey: ["baseline-status"] });
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
  const baselineStatus = baselineStatusQuery.data;
  const baselineMix = baselineStatus?.event_mix ?? {};
  const connectionLabel =
    dataSource === "live" && !liveStream ? "Paused" : humanizeIdentifier(connectionState);
  const connectionTone = dataSource === "live" && !liveStream ? "neutral" : toneForConnection(connectionState);

  function confirmClearSeededData() {
    if (
      window.confirm(
        "Clear seeded demo events, demo alerts, and demo cases from the live datastore?",
      )
    ) {
      clearSeededMutation.mutate();
    }
  }

  function confirmClearLiveData() {
    if (
      window.confirm(
        "Clear all indexed events, alerts, cases, and linked investigation records? The live baseline emitter will start repopulating normal telemetry afterward.",
      )
    ) {
      clearLiveMutation.mutate();
    }
  }

  return (
    <div className="page-grid">
      <PageIntro
        eyebrow="Settings"
        title="Operations settings"
        description="Manage live telemetry controls, operational baseline health, and datastore maintenance. Demo tooling is available separately when you explicitly need it."
        actions={
          <StatusBadge
            label={dataSource === "synthetic" ? "Synthetic mode active" : "Live telemetry"}
            tone={dataSource === "synthetic" ? "medium" : "low"}
            tooltip={
              dataSource === "synthetic"
                ? "The workspace is currently using bundled synthetic data instead of the live backend responses."
                : "The workspace is currently sourcing data from live backend APIs and the baseline telemetry emitter."
            }
          />
        }
      />

      <div className="content-grid content-grid--wide">
        <DataPanel subtitle="Primary controls for the live workspace" title="Operations workspace">
          <div className="settings-stack">
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
              <strong>{dataSource === "synthetic" ? "Synthetic mode" : "Live telemetry"}</strong>
              <StatusBadge
                label={dataSource === "synthetic" ? "Synthetic dataset" : "Live dataset"}
                tone={dataSource === "synthetic" ? "medium" : "neutral"}
                tooltip="Controls whether each page reads bundled synthetic data or backend API responses."
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
              <span>Mode guidance</span>
              <strong>{dataSource === "synthetic" ? "Presentation mode" : "Operations mode"}</strong>
              <StatusBadge
                label={dataSource === "synthetic" ? "Synthetic active" : "Live default"}
                tone={dataSource === "synthetic" ? "medium" : "connected"}
                tooltip="Synthetic mode is available for walkthroughs, but the default workspace is tuned for live operations."
              />
            </article>
          </div>
        </DataPanel>
      </div>

      <div className="content-grid content-grid--wide">
        <DataPanel
          subtitle="Operational baseline feeding the real ingestion path"
          title="Live telemetry baseline"
        >
          <div className="watchlist-grid">
            <article className="watchlist-card">
              <span>Emitter</span>
              <strong>{baselineStatus?.running ? "Online" : "Standby"}</strong>
              <StatusBadge
                label={baselineStatus?.running ? "live ingestion" : "idle"}
                tone={baselineStatus?.running ? "connected" : "neutral"}
                tooltip="Shows whether the live operational baseline is actively sending events through the ingestion service."
              />
              <p>
                {baselineStatus?.last_ingested_at
                  ? `Last batch ${new Date(baselineStatus.last_ingested_at).toLocaleString()}`
                  : "No baseline batch has been ingested yet."}
              </p>
            </article>
            <article className="watchlist-card">
              <span>Health probes</span>
              <strong>{baselineMix.service_health ?? 0}</strong>
              <p>
                {baselineStatus?.last_checks?.mysql || baselineStatus?.last_checks?.redis
                  ? Object.entries(baselineStatus?.last_checks ?? {})
                      .map(([name, status]) => `${name}: ${status}`)
                      .join(" · ")
                  : "MySQL and Redis checks will appear after the first live batch."}
              </p>
            </article>
            <article className="watchlist-card">
              <span>Heartbeats</span>
              <strong>{baselineMix.service_heartbeat ?? 0}</strong>
              <p>{baselineStatus?.monitored_services.length ?? 0} monitored services reporting</p>
            </article>
            <article className="watchlist-card">
              <span>Normal flows</span>
              <strong>{baselineMix.network_flow ?? 0}</strong>
              <p>{baselineStatus?.last_batch_size ?? 0} events in the latest live batch</p>
            </article>
          </div>
        </DataPanel>
      </div>

      <DataPanel subtitle="Remove persisted data from the live datastore" title="Data clearing">
        <div className="settings-stack">
          <label className="setting-row">
            <div>
              <strong>Clear live datastore</strong>
              <p>Remove all indexed events, alerts, cases, and investigation records, then let the live baseline repopulate normal telemetry.</p>
            </div>
            <button
              className="ghost-button ghost-button--compact"
              disabled={clearLiveMutation.isPending}
              onClick={confirmClearLiveData}
              type="button"
            >
              {clearLiveMutation.isPending ? "Clearing…" : "Clear live data"}
            </button>
          </label>
        </div>
      </DataPanel>

      <DataPanel subtitle="Secondary tools for walkthroughs and seeded scenario testing" title="Demo and synthetic tooling">
        <details className="settings-disclosure">
          <summary className="settings-disclosure__summary">
            <div>
              <strong>Show demo controls</strong>
              <p>Keep these hidden during normal operations. Open only when you need seeded data, screenshots, or synthetic walkthroughs.</p>
            </div>
            <StatusBadge
              label={dataSource === "synthetic" ? "synthetic mode active" : "hidden by default"}
              tone={dataSource === "synthetic" ? "medium" : "neutral"}
            />
          </summary>

          <div className="settings-disclosure__content">
            <div className="settings-stack">
              <label className="setting-row">
                <div>
                  <strong>Workspace data source</strong>
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
                    title="Use bundled synthetic telemetry for walkthroughs and presentation captures."
                    type="button"
                  >
                    Synthetic
                  </button>
                </div>
              </label>

              <label className="setting-row">
                <div>
                  <strong>Synthetic intensity</strong>
                  <p>Higher values increase chart volumes and queue density in synthetic mode.</p>
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
                  <strong>Presentation preference</strong>
                  <p>Mark synthetic mode as the preferred option when you are preparing walkthrough captures.</p>
                </div>
                <button
                  className="ghost-button ghost-button--compact"
                  onClick={() => setPreferSyntheticForScreenshots(!preferSyntheticForScreenshots)}
                  type="button"
                >
                  {preferSyntheticForScreenshots ? "Preferred" : "Manual"}
                </button>
              </label>
            </div>

            <div className="watchlist-grid">
              <article className="watchlist-card">
                <span>Generator</span>
                <strong>{liveDemo?.generator_status ? humanizeIdentifier(liveDemo.generator_status) : "Not available"}</strong>
                <StatusBadge
                  label={liveDemo?.enabled ? "enabled" : "disabled"}
                  tone={liveDemo?.enabled ? "connected" : "neutral"}
                  tooltip="Shows whether the backend synthetic generator is actively producing new telemetry."
                />
              </article>
              <article className="watchlist-card">
                <span>Seeded events</span>
                <strong>{demoCounts?.events ?? 0}</strong>
                <p>Persisted seeded telemetry</p>
              </article>
              <article className="watchlist-card">
                <span>Seeded alerts</span>
                <strong>{demoCounts?.alerts ?? 0}</strong>
                <p>Detections generated from seeded events</p>
              </article>
              <article className="watchlist-card">
                <span>Scenario cases</span>
                <strong>{demoCounts?.cases ?? 0}</strong>
                <p>{liveDemo?.seeded_at ? new Date(liveDemo.seeded_at).toLocaleString() : "Not seeded yet"}</p>
              </article>
            </div>

            <div className="settings-stack">
              <label className="setting-row">
                <div>
                  <strong>Seed scenario data</strong>
                  <p>Inject a bundled attack storyline into the live datastore for walkthroughs and validation.</p>
                </div>
                <button
                  className="primary-button"
                  disabled={seedMutation.isPending}
                  onClick={() => seedMutation.mutate()}
                  title="Inject the bundled attack storyline into the live backend so events, alerts, cases, and ATT&CK coverage populate together."
                  type="button"
                >
                  {seedMutation.isPending ? "Seeding…" : "Seed scenario data"}
                </button>
              </label>

              <label className="setting-row">
                <div>
                  <strong>Synthetic generator</strong>
                  <p>Start or stop background synthetic ingestion while staying on the live backend path.</p>
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
                  title="Toggle the backend synthetic generator without leaving live API mode."
                  type="button"
                >
                  {liveDemo?.enabled ? "Stop generator" : "Start generator"}
                </button>
              </label>

              <label className="setting-row">
                <div>
                  <strong>Sync generator intensity</strong>
                  <p>Push the current local synthetic intensity into the backend runtime.</p>
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

              <label className="setting-row">
                <div>
                  <strong>Clear seeded scenario data</strong>
                  <p>Remove demo-seeded events, alerts, and cases while leaving the live baseline telemetry intact.</p>
                </div>
                <button
                  className="ghost-button ghost-button--compact"
                  disabled={clearSeededMutation.isPending}
                  onClick={confirmClearSeededData}
                  type="button"
                >
                  {clearSeededMutation.isPending ? "Clearing…" : "Clear seeded data"}
                </button>
              </label>
            </div>
          </div>
        </details>
      </DataPanel>

      <DataPanel subtitle={dataSource === "synthetic" ? "Synthetic roster active for walkthrough mode" : "Analyst data from the live settings API"} title="Analyst management">
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
