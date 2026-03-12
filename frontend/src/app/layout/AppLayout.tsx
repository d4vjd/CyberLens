// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import { NavLink, Outlet } from "react-router-dom";

import { useAlertStream } from "../providers/AlertStreamProvider";
import { useDemoStore } from "../store/demoStore";
import { useThemeStore } from "../store/themeStore";
import { navIcons } from "../../shared/components/Icons";
import { StatusBadge } from "../../shared/components/StatusBadge";
import { Tooltip } from "../../shared/components/Tooltip";
import { humanizeIdentifier } from "../../shared/utils/format";

const navigation = [
  { to: "/", label: "Overview", section: "monitor" },
  { to: "/events", label: "Events", section: "monitor" },
  { to: "/alerts", label: "Alerts", section: "monitor" },
  { to: "/mitre", label: "MITRE ATT&CK", section: "investigate" },
  { to: "/cases", label: "Cases", section: "investigate" },
  { to: "/rules", label: "Rules", section: "investigate" },
  { to: "/analytics", label: "Analytics", section: "investigate" },
  { to: "/settings", label: "Settings", section: "configure" },
];

const sectionLabels: Record<string, string> = {
  monitor: "Monitor",
  investigate: "Investigate",
  configure: "Configure",
};

function connectionTone(state: string) {
  if (state === "connected" || state === "synthetic") {
    return "connected";
  }
  if (state === "reconnecting" || state === "connecting") {
    return "medium";
  }
  return "offline";
}

function connectionLabel(state: string) {
  switch (state) {
    case "synthetic":
      return "Synthetic feed";
    case "connected":
      return "Alert stream live";
    case "reconnecting":
      return "Alert stream reconnecting";
    case "connecting":
      return "Connecting to alerts";
    default:
      return "Alert stream offline";
  }
}

function workspaceSignalLabel(
  dataSource: "live" | "synthetic",
  liveStream: boolean,
  connectionState: string,
) {
  if (dataSource === "synthetic") {
    return "Synthetic dataset active";
  }

  if (!liveStream) {
    return "Live alert stream paused";
  }

  if (connectionState === "connected") {
    return "Live alert stream connected";
  }

  if (connectionState === "reconnecting") {
    return "Reconnecting to live alerts";
  }

  if (connectionState === "connecting") {
    return "Connecting to live alerts";
  }

  return "Live alert stream unavailable";
}

export function AppLayout() {
  const { theme, toggleTheme } = useThemeStore();
  const { dataSource, setDataSource, intensity, liveStream } = useDemoStore();
  const { connectionState, unseenCount } = useAlertStream();
  const streamTone = dataSource === "live" && !liveStream ? "neutral" : connectionTone(connectionState);
  const streamLabel =
    dataSource === "live" && !liveStream ? "Alert stream paused" : connectionLabel(connectionState);

  let currentSection = "";

  return (
    <div className="app-shell" data-theme={theme}>
      <aside className="sidebar">
        <div className="brand-mark">
          <span className="brand-mark__chip">CL</span>
          <div>
            <h1>CyberLens</h1>
            <p className="brand-mark__version">Security Intelligence Platform</p>
          </div>
        </div>

        <nav className="sidebar-nav">
          {navigation.map((item) => {
            const showSectionLabel = item.section !== currentSection;
            currentSection = item.section;

            const badge =
              item.to === "/events"
                ? dataSource === "synthetic"
                  ? "Demo"
                  : "Live"
                : item.to === "/alerts"
                  ? unseenCount > 0
                    ? `${unseenCount} new`
                    : "Idle"
                  : item.to === "/settings"
                    ? humanizeIdentifier(theme)
                    : "";

            const Icon = navIcons[item.to];

            return (
              <div key={item.to}>
                {showSectionLabel ? (
                  <p className="sidebar-section-label">{sectionLabels[item.section]}</p>
                ) : null}
                <NavLink
                  className={({ isActive }) =>
                    isActive ? "sidebar-link sidebar-link--active" : "sidebar-link"
                  }
                  to={item.to}
                >
                  {Icon ? (
                    <span className="sidebar-link__icon">
                      <Icon size={16} />
                    </span>
                  ) : null}
                  <span className="sidebar-link__label">{item.label}</span>
                  {badge ? (
                    <Tooltip
                      content={
                        item.to === "/events"
                          ? dataSource === "synthetic"
                            ? "Synthetic walkthrough data is currently powering the event stream."
                            : "Live API-backed event telemetry is currently active."
                          : item.to === "/alerts"
                            ? unseenCount > 0
                              ? `${unseenCount} recent alert updates have not been reviewed yet.`
                              : "No unseen alert-stream updates are waiting in the queue."
                            : `Current theme: ${humanizeIdentifier(theme)}. Synthetic intensity remains set to ${intensity}/10 in Settings.`
                      }
                    >
                      <span className="sidebar-badge">{badge}</span>
                    </Tooltip>
                  ) : null}
                </NavLink>
              </div>
            );
          })}
        </nav>

        <div className="sidebar-panel">
          <strong>{dataSource === "synthetic" ? "Synthetic walkthrough" : "Live telemetry"}</strong>
          <p>
            {dataSource === "synthetic"
              ? "Synthetic storylines are active across all views so the console stays fully populated."
              : "Live APIs are active. Switch to the synthetic walkthrough when you need richer showcase telemetry."}
          </p>
          <div className="sidebar-panel__chips">
            <StatusBadge
              label={streamLabel}
              tone={streamTone}
              tooltip="Current alert-stream state. Synthetic mode bypasses the live WebSocket and keeps the console populated from bundled data."
            />
            <StatusBadge
              label={`Intensity ${intensity}/10`}
              tone="neutral"
              tooltip="Preview density controls how much synthetic telemetry appears across charts, queues, and cases."
            />
          </div>
          <button
            className="ghost-button"
            onClick={() => setDataSource(dataSource === "live" ? "synthetic" : "live")}
            title={
              dataSource === "live"
                ? "Swap the UI into bundled demo data with fuller queues and richer charts."
                : "Return the UI to API-backed live telemetry."
            }
            type="button"
          >
            {dataSource === "live" ? "Use synthetic walkthrough" : "Return to live telemetry"}
          </button>
          <button
            className="ghost-button"
            onClick={toggleTheme}
            title={`Switch the workspace to the ${theme === "night" ? "dawn" : "night"} theme.`}
            type="button"
          >
            {theme === "night" ? "Use dawn theme" : "Use night theme"}
          </button>
        </div>
      </aside>

      <main className="workspace">
        <header className="workspace-header">
          <div>
            <p className="eyebrow">Portfolio SIEM</p>
            <h2>Analyst Console</h2>
          </div>
          <div className="workspace-header__actions">
            <div
              className="signal-pill"
              title={
                dataSource === "synthetic"
                  ? "Bundled synthetic data is active across the console."
                  : liveStream
                    ? `Current alert bridge state: ${connectionLabel(connectionState).toLowerCase()}.`
                    : "The live WebSocket bridge is currently paused in Settings."
              }
            >
              <span className={`signal-dot signal-dot--${streamTone === "neutral" ? "medium" : streamTone}`} />
              {workspaceSignalLabel(dataSource, liveStream, connectionState)}
            </div>
          </div>
        </header>

        <Outlet />
      </main>
    </div>
  );
}
