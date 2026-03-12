// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";

import { useAlertStream } from "../../app/providers/AlertStreamProvider";
import { useDemoStore } from "../../app/store/demoStore";
import { DataPanel } from "../../shared/components/DataPanel";
import { DataTable } from "../../shared/components/DataTable";
import { PageIntro } from "../../shared/components/PageIntro";
import { SearchInput } from "../../shared/components/SearchInput";
import { StatusBadge } from "../../shared/components/StatusBadge";
import { useDebounce } from "../../shared/hooks/useDebounce";
import type { AlertListResponse, AlertRecord } from "../../shared/types";
import { fetchJson, postJson } from "../../shared/utils/api";
import { getSyntheticAlerts } from "../../shared/utils/mockData";

async function fetchLiveAlerts() {
  return fetchJson<AlertListResponse>("/alerts?limit=50&offset=0");
}

export function AlertsPage() {
  const queryClient = useQueryClient();
  const dataSource = useDemoStore((state) => state.dataSource);
  const [search, setSearch] = useState("");
  const [severity, setSeverity] = useState("");
  const [status, setStatus] = useState("");
  const [selectedAlert, setSelectedAlert] = useState<AlertRecord | null>(null);
  const debouncedSearch = useDebounce(search, 250);
  const { recentAlerts, unseenCount, clearUnseen } = useAlertStream();
  const [actionMessage, setActionMessage] = useState("");

  const { data, isLoading, isError } = useQuery({
    queryKey: ["alerts", dataSource],
    queryFn: () =>
      dataSource === "synthetic" ? Promise.resolve(getSyntheticAlerts()) : fetchLiveAlerts(),
  });

  const escalateMutation = useMutation({
    mutationFn: (alert: AlertRecord) =>
      postJson(`/incidents/from-alerts/${alert.id}`, {
        actor: "ahassan",
        assigned_to: "ahassan",
      }),
    onSuccess: async () => {
      setActionMessage("Alert escalated to a live case.");
      await queryClient.invalidateQueries({ queryKey: ["cases", "live"] });
      await queryClient.invalidateQueries({ queryKey: ["alerts"] });
    },
  });

  const filteredAlerts = useMemo(() => {
    const items = data?.items ?? [];
    return items.filter((alert) => {
      if (severity && alert.severity !== severity) {
        return false;
      }
      if (status && alert.status !== status) {
        return false;
      }
      if (!debouncedSearch) {
        return true;
      }
      const needle = debouncedSearch.toLowerCase();
      return [alert.title, alert.source_ip, alert.mitre_tactic, alert.mitre_technique_id, alert.assigned_to]
        .filter(Boolean)
        .some((value) => value!.toLowerCase().includes(needle));
    });
  }, [data?.items, debouncedSearch, severity, status]);

  useEffect(() => {
    if (!filteredAlerts.length) {
      setSelectedAlert(null);
      return;
    }

    setSelectedAlert((current) => {
      if (!current) {
        return filteredAlerts[0];
      }
      return filteredAlerts.find((item) => item.id === current.id) ?? filteredAlerts[0];
    });
  }, [filteredAlerts]);

  return (
    <div className="page-grid">
      <PageIntro
        eyebrow="Alerts"
        title="Detection queue"
        description="Review detections with ATT&CK context, inspect matched events, and use synthetic mode when you want a richer incident queue for demos."
        actions={
          <div className="panel-badge-row">
            <StatusBadge
              label={dataSource === "synthetic" ? "Synthetic queue" : `${unseenCount} unseen stream updates`}
              tone={dataSource === "synthetic" ? "connected" : unseenCount ? "high" : "neutral"}
            />
            <StatusBadge label={`${filteredAlerts.length} visible`} tone="neutral" />
          </div>
        }
      />

      {dataSource === "live" && recentAlerts.length ? (
        <DataPanel
          actions={
            <button className="ghost-button ghost-button--compact" onClick={clearUnseen} type="button">
              Clear highlight
            </button>
          }
          subtitle="Fresh detections received over the WebSocket bridge"
          title="Recent stream updates"
        >
          <div className="list-panel">
            {recentAlerts.slice(0, 3).map((alert) => (
              <article className="list-item" key={alert.alert_uid}>
                <div>
                  <strong>{alert.title}</strong>
                  <p>
                    {alert.source_ip ?? "n/a"} · {alert.mitre_technique_id ?? "No ATT&CK mapping"}
                  </p>
                </div>
                <StatusBadge label={alert.severity} tone={alert.severity} />
              </article>
            ))}
          </div>
        </DataPanel>
      ) : null}

      {actionMessage ? (
        <DataPanel subtitle="Latest workflow update" title="Escalation result">
          <p className="table-message">{actionMessage}</p>
        </DataPanel>
      ) : null}

      <DataPanel subtitle="Filter by search text, severity, or analyst status" title="Queue controls">
        <div className="filter-grid">
          <SearchInput onChange={setSearch} placeholder="Search title, IP, technique, or analyst" value={search} />
          <select className="filter-input" onChange={(event) => setSeverity(event.target.value)} value={severity}>
            <option value="">All severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <select className="filter-input" onChange={(event) => setStatus(event.target.value)} value={status}>
            <option value="">All statuses</option>
            <option value="new">New</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="investigating">Investigating</option>
            <option value="resolved">Resolved</option>
            <option value="false_positive">False positive</option>
          </select>
        </div>
      </DataPanel>

      {isLoading ? <p className="table-message">Loading alert queue…</p> : null}
      {isError ? <p className="table-message">Failed to load alerts from the selected data source.</p> : null}

      {!isLoading && !isError ? (
        <div className="content-grid content-grid--wide">
          <DataPanel subtitle="Latest detections with ATT&CK mapping" title="Queue">
            <DataTable
              columns={[
                {
                  header: "Created",
                  render: (alert) => new Date(alert.created_at).toLocaleString(),
                },
                {
                  header: "Title",
                  render: (alert) => alert.title,
                },
                {
                  header: "Source",
                  render: (alert) => alert.source_ip ?? "n/a",
                },
                {
                  header: "ATT&CK",
                  render: (alert) =>
                    alert.mitre_technique_id
                      ? `${alert.mitre_tactic} / ${alert.mitre_technique_id}`
                      : "n/a",
                },
                {
                  header: "Status",
                  render: (alert) => <StatusBadge label={alert.status} tone="neutral" />,
                },
                {
                  header: "Severity",
                  render: (alert) => <StatusBadge label={alert.severity} tone={alert.severity} />,
                },
              ]}
              emptyMessage="No alerts matched the current filter set."
              items={filteredAlerts}
              onRowClick={setSelectedAlert}
              rowKey={(alert) => alert.alert_uid}
            />
          </DataPanel>

          <DataPanel
            subtitle="Selected alert details and matched telemetry"
            title={selectedAlert ? selectedAlert.title : "Alert detail"}
          >
            {selectedAlert ? (
              <div className="detail-stack">
                <div className="panel-badge-row">
                  <StatusBadge label={selectedAlert.severity} tone={selectedAlert.severity} />
                  <StatusBadge label={selectedAlert.status} tone="neutral" />
                  <StatusBadge
                    label={selectedAlert.mitre_technique_id ?? "Unmapped"}
                    tone={selectedAlert.mitre_technique_id ? "medium" : "neutral"}
                  />
                </div>
                <div className="detail-grid">
                  <div>
                    <span className="detail-label">Source IP</span>
                    <strong>{selectedAlert.source_ip ?? "n/a"}</strong>
                  </div>
                  <div>
                    <span className="detail-label">Assigned</span>
                    <strong>{selectedAlert.assigned_to ?? "Unassigned"}</strong>
                  </div>
                  <div>
                    <span className="detail-label">Created</span>
                    <strong>{new Date(selectedAlert.created_at).toLocaleString()}</strong>
                  </div>
                  <div>
                    <span className="detail-label">Rule ID</span>
                    <strong>{selectedAlert.rule_id}</strong>
                  </div>
                </div>
                <div className="matched-events">
                  <span className="detail-label">Matched events</span>
                  <pre className="code-surface code-surface--compact">
                    {JSON.stringify(selectedAlert.matched_events, null, 2)}
                  </pre>
                </div>
                {dataSource === "live" ? (
                  <button
                    className="primary-button"
                    disabled={escalateMutation.isPending}
                    onClick={() => escalateMutation.mutate(selectedAlert)}
                    type="button"
                  >
                    {escalateMutation.isPending ? "Creating case…" : "Create live case"}
                  </button>
                ) : (
                  <button className="primary-button" type="button">
                    Open synthetic case draft
                  </button>
                )}
              </div>
            ) : (
              <p className="table-message">Select an alert from the queue to inspect it.</p>
            )}
          </DataPanel>
        </div>
      ) : null}
    </div>
  );
}