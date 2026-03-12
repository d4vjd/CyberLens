// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import { NavLink, Outlet } from "react-router-dom";

import { useAlertStream } from "../providers/AlertStreamProvider";
import { useDemoStore } from "../store/demoStore";
import { useThemeStore } from "../store/themeStore";
import { StatusBadge } from "../../shared/components/StatusBadge";

const navigation = [
  { to: "/", label: "Overview" },
  { to: "/events", label: "Events" },
  { to: "/alerts", label: "Alerts" },
  { to: "/mitre", label: "MITRE ATT&CK" },
  { to: "/cases", label: "Cases" },
  { to: "/rules", label: "Rules" },
  { to: "/analytics", label: "Analytics" },
  { to: "/settings", label: "Settings" },
];

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
      return "WebSocket live";
    case "reconnecting":
      return "Reconnecting";
    case "connecting":
      return "Connecting";
    default:
      return "Offline";
  }
}

export function AppLayout() {
  const { theme, toggleTheme } = useThemeStore();
  const { dataSource, setDataSource, intensity } = useDemoStore();
  const { connectionState, unseenCount } = useAlertStream();

  return (
    <div className="app-shell" data-theme={theme}>
      <aside className="sidebar">
        <div className="brand-mark">
          <span className="brand-mark__chip">CL</span>
          <div>
            <p className="eyebrow">Security Intelligence</p>
            <h1>CyberLens</h1>
          </div>
        </div>

        <nav className="sidebar-nav">
          {navigation.map((item) => {
            const badge =
              item.to === "/events"
                ? dataSource === "synthetic"
                  ? "Synth"
                  : "Live"
                : item.to === "/alerts"
                  ? unseenCount > 0
                    ? `+${unseenCount}`
                    : "Queue"
                  : item.to === "/settings"
                    ? `L${intensity}`
                    : "";

            return (
              <NavLink
                key={item.to}
                className={({ isActive }) =>
                  isActive ? "sidebar-link sidebar-link--active" : "sidebar-link"
                }
                to={item.to}
              >
                <span>{item.label}</span>
                {badge ? <span className="sidebar-badge">{badge}</span> : null}
              </NavLink>
            );
          })}
        </nav>

        <div className="sidebar-panel">
          <p className="eyebrow">Operational Posture</p>
          <strong>{dataSource === "synthetic" ? "Screenshot mode ready" : "Live telemetry mode"}</strong>
          <p>
            {dataSource === "synthetic"
              ? "Synthetic attack progression is enabled across the dashboard so every screen stays populated."
              : "Live API mode is active. Toggle synthetic mode whenever you need fully populated portfolio screenshots."}
          </p>
          <div className="sidebar-panel__chips">
            <StatusBadge label={connectionLabel(connectionState)} tone={connectionTone(connectionState)} />
            <StatusBadge label={`Intensity ${intensity}`} tone="neutral" />
          </div>
          <button
            className="ghost-button"
            onClick={() => setDataSource(dataSource === "live" ? "synthetic" : "live")}
            type="button"
          >
            {dataSource === "live" ? "Use synthetic data" : "Return to live APIs"}
          </button>
          <button className="ghost-button" onClick={toggleTheme} type="button">
            Switch to {theme === "night" ? "Dawn" : "Night"} mode
          </button>
        </div>
      </aside>

      <main className="workspace">
        <header className="workspace-header">
          <div>
            <p className="eyebrow">Portfolio SIEM Project</p>
            <h2>Analyst Console</h2>
          </div>
          <div className="workspace-header__actions">
            <div className="signal-pill">
              <span className={`signal-dot signal-dot--${connectionTone(connectionState)}`} />
              {dataSource === "synthetic"
                ? "Synthetic dataset rendering full workflow coverage"
                : "Streaming bridge connected to live alert queue"}
            </div>
            <button className="primary-button" onClick={() => setDataSource("synthetic")} type="button">
              Show synthetic walkthrough
            </button>
          </div>
        </header>

        <Outlet />
      </main>
    </div>
  );
}