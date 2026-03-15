// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import { NavLink, Outlet } from "react-router-dom";

import { useAlertStream } from "../providers/AlertStreamProvider";
import { useDemoStore } from "../store/demoStore";
import { useThemeStore } from "../store/themeStore";
import { IconMoon, IconSun, navIcons } from "../../shared/components/Icons";
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
    return "Live stream paused";
  }

  if (connectionState === "connected") {
    return "Operational telemetry live";
  }

  if (connectionState === "reconnecting") {
    return "Reconnecting live telemetry";
  }

  if (connectionState === "connecting") {
    return "Connecting telemetry stream";
  }

  return "Telemetry stream unavailable";
}

export function AppLayout() {
  const { theme, toggleTheme } = useThemeStore();
  const { dataSource, liveStream } = useDemoStore();
  const { connectionState, unseenCount } = useAlertStream();
  const streamTone = dataSource === "live" && !liveStream ? "neutral" : connectionTone(connectionState);
  const streamLabel =
    dataSource === "live" && !liveStream ? "Alert stream paused" : connectionLabel(connectionState);

  let currentSection = "";

  return (
    <div className="app-shell" data-theme={theme}>
      <aside className="sidebar">
        <div className="brand-mark">
          <img
            alt=""
            aria-hidden="true"
            className="brand-mark__logo"
            src="/branding/cyberlens-mark.svg"
          />
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
                            : `Current theme: ${humanizeIdentifier(theme)}. Additional workspace controls are available in Settings.`
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

      </aside>

      <main className="workspace">
        <header className="workspace-header">
          <div>
            <p className="eyebrow">Security Operations Platform</p>
            <h2>Operational telemetry</h2>
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
            <Tooltip
              content={
                theme === "night"
                  ? "Switch to the dawn theme."
                  : "Switch back to the night theme."
              }
            >
              <button
                aria-label={theme === "night" ? "Use dawn theme" : "Use night theme"}
                className="icon-button"
                onClick={toggleTheme}
                type="button"
              >
                {theme === "night" ? <IconSun size={16} /> : <IconMoon size={16} />}
              </button>
            </Tooltip>
          </div>
        </header>

        <Outlet />
      </main>
    </div>
  );
}
