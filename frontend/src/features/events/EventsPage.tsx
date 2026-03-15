// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { useDemoStore } from "../../app/store/demoStore";
import { DataPanel } from "../../shared/components/DataPanel";
import { DataTable } from "../../shared/components/DataTable";
import { PageIntro } from "../../shared/components/PageIntro";
import { Pagination } from "../../shared/components/Pagination";
import { SearchInput } from "../../shared/components/SearchInput";
import { StatusBadge } from "../../shared/components/StatusBadge";
import { useDebounce } from "../../shared/hooks/useDebounce";
import { usePagination } from "../../shared/hooks/usePagination";
import type { EventListResponse, EventRecord } from "../../shared/types";
import { buildQuery, fetchJson } from "../../shared/utils/api";
import { formatDateTime, formatFlow, formatNullable, humanizeIdentifier } from "../../shared/utils/format";
import { getSyntheticEvents } from "../../shared/utils/mockData";

async function fetchLiveEvents(filters: {
  search: string;
  eventType: string;
  sourceSystem: string;
  severity: string;
  offset: number;
  limit: number;
}) {
  const query = buildQuery({
    search: filters.search,
    event_type: filters.eventType,
    source_system: filters.sourceSystem,
    severity: filters.severity,
    offset: filters.offset,
    limit: filters.limit,
  });

  return fetchJson<EventListResponse>(`/events${query}`);
}

export function EventsPage() {
  const dataSource = useDemoStore((state) => state.dataSource);
  const liveStream = useDemoStore((state) => state.liveStream);
  const { page, pageSize, setPage, reset } = usePagination(10);
  const [search, setSearch] = useState("");
  const [eventType, setEventType] = useState("");
  const [sourceSystem, setSourceSystem] = useState("");
  const [severity, setSeverity] = useState("");
  const [selectedEvent, setSelectedEvent] = useState<EventRecord | null>(null);
  const debouncedSearch = useDebounce(search, 250);

  useEffect(() => {
    reset();
  }, [debouncedSearch, eventType, sourceSystem, severity, reset]);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["events", dataSource, debouncedSearch, eventType, sourceSystem, severity, page, pageSize],
    queryFn: () =>
      dataSource === "synthetic"
        ? Promise.resolve(
            getSyntheticEvents({
              search: debouncedSearch,
              eventType,
              sourceSystem,
              severity,
              offset: page * pageSize,
              limit: pageSize,
            }),
          )
        : fetchLiveEvents({
            search: debouncedSearch,
            eventType,
            sourceSystem,
            severity,
            offset: page * pageSize,
            limit: pageSize,
          }),
    refetchInterval: dataSource === "live" ? 5000 : false,
  });

  useEffect(() => {
    if (!data?.items.length) {
      setSelectedEvent(null);
      return;
    }

    setSelectedEvent((current) => {
      if (!current) {
        return data.items[0];
      }
      return data.items.find((item) => item.id === current.id) ?? data.items[0];
    });
  }, [data]);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / pageSize)) : 1;

  return (
    <div className="page-grid">
      <PageIntro
        eyebrow="Events"
        title={dataSource === "synthetic" ? "Normalized event stream" : "Live event stream"}
        description={
          dataSource === "synthetic"
            ? "Filter the raw intake, inspect normalized fields, and switch to synthetic telemetry whenever you need a fully populated walkthrough."
            : "Inspect the live intake, review normalized payloads, and follow routine service activity through the real ingestion pipeline."
        }
        actions={
          <div className="panel-badge-row">
            <StatusBadge
              label={
                dataSource === "synthetic"
                  ? "Synthetic feed"
                  : liveStream
                    ? "Live feed enabled"
                    : "Live feed paused"
              }
              tone={dataSource === "synthetic" ? "connected" : liveStream ? "low" : "neutral"}
              tooltip={
                dataSource === "synthetic"
                  ? "Events are sourced from the bundled showcase dataset."
                  : liveStream
                    ? "The page is reading the live ingestion pipeline while the alert bridge remains enabled."
                    : "The page is reading live APIs, but the background alert stream is paused."
              }
            />
            <StatusBadge
              label={`${data?.total ?? 0} indexed`}
              tone="neutral"
              tooltip="Total events returned by the current filter set."
            />
          </div>
        }
      />

      <DataPanel
        subtitle="Filter by search term, type, source, or severity"
        title={dataSource === "synthetic" ? "Search controls" : "Live filters"}
      >
        <div className="filter-grid">
          <SearchInput
            onChange={setSearch}
            placeholder="Search raw log, host, user, or IP"
            value={search}
          />
          <input
            className="filter-input"
            onChange={(event) => setEventType(event.target.value)}
            placeholder="Event type"
            title="Filter by normalized event type such as vpn_login, authentication, or data_transfer."
            value={eventType}
          />
          <input
            className="filter-input"
            onChange={(event) => setSourceSystem(event.target.value)}
            placeholder="Source system"
            title="Filter by parser/source system such as syslog, firewall, windows_event, or json_generic."
            value={sourceSystem}
          />
          <select
            className="filter-input"
            onChange={(event) => setSeverity(event.target.value)}
            title="Limit the table to a single severity band."
            value={severity}
          >
            <option value="">All severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
      </DataPanel>

      {isLoading ? <div className="loading-state"><span className="loading-spinner" />Loading event stream…</div> : null}
      {isError ? <div className="error-state">Failed to load events from the selected data source.</div> : null}

      {!isLoading && !isError && data ? (
        <div className="content-grid content-grid--wide">
          <DataPanel
            subtitle="Newest events first. Click any row to inspect the normalized payload."
            title="Recent events"
          >
            <DataTable
              columns={[
                {
                  header: "Timestamp",
                  render: (event) => formatDateTime(event.timestamp),
                },
                {
                  header: "Type",
                  render: (event) => humanizeIdentifier(event.event_type),
                },
                {
                  header: "Source",
                  render: (event) => humanizeIdentifier(event.source_system),
                },
                {
                  header: "Flow",
                  render: (event) => formatFlow(event.source_ip, event.dest_ip),
                },
                {
                  header: "Action",
                  render: (event) => formatNullable(event.action, "Not observed"),
                },
                {
                  header: "Severity",
                  render: (event) => (
                    <StatusBadge
                      label={humanizeIdentifier(event.severity)}
                      tone={event.severity}
                      tooltip={event.message ?? "Severity assigned during normalization."}
                    />
                  ),
                },
              ]}
              emptyMessage="No events matched the current filters."
              items={data.items}
              onRowClick={setSelectedEvent}
              rowTitle={(event) => event.message ?? "Click to inspect normalized event details."}
              rowKey={(event) => event.id}
              selectedRowKey={selectedEvent?.id ?? null}
            />

            <div className="table-toolbar">
              <p className="table-meta">
                Showing {data.items.length} of {data.total} events
              </p>
              <Pagination
                currentPage={page + 1}
                onNext={() => setPage((current) => current + 1)}
                onPrevious={() => setPage((current) => Math.max(0, current - 1))}
                totalPages={totalPages}
              />
            </div>
          </DataPanel>

          <DataPanel
            subtitle="Selected event detail"
            title={selectedEvent ? `${humanizeIdentifier(selectedEvent.event_type)} · Event ${selectedEvent.id}` : "Event detail"}
          >
            {selectedEvent ? (
              <div className="detail-stack">
                <div className="detail-grid">
                  <div>
                    <span className="detail-label">Host</span>
                    <strong>{formatNullable(selectedEvent.hostname)}</strong>
                  </div>
                  <div>
                    <span className="detail-label">User</span>
                    <strong>{formatNullable(selectedEvent.username)}</strong>
                  </div>
                  <div>
                    <span className="detail-label">Source system</span>
                    <strong>{humanizeIdentifier(selectedEvent.source_system)}</strong>
                  </div>
                  <div>
                    <span className="detail-label">Severity</span>
                    <StatusBadge
                      label={humanizeIdentifier(selectedEvent.severity)}
                      tone={selectedEvent.severity}
                      tooltip="Severity assigned during parsing and detection correlation."
                    />
                  </div>
                  <div>
                    <span className="detail-label">Source IP</span>
                    <strong>{formatNullable(selectedEvent.source_ip)}</strong>
                  </div>
                  <div>
                    <span className="detail-label">Destination IP</span>
                    <strong>{formatNullable(selectedEvent.dest_ip)}</strong>
                  </div>
                  <div>
                    <span className="detail-label">Protocol</span>
                    <strong>{formatNullable(selectedEvent.protocol, "Not observed")}</strong>
                  </div>
                  <div>
                    <span className="detail-label">Destination port</span>
                    <strong>{formatNullable(selectedEvent.dest_port, "Not observed")}</strong>
                  </div>
                  <div>
                    <span className="detail-label">Action</span>
                    <strong>{formatNullable(selectedEvent.action, "Not observed")}</strong>
                  </div>
                  <div>
                    <span className="detail-label">Observed at</span>
                    <strong>{formatDateTime(selectedEvent.timestamp)}</strong>
                  </div>
                </div>
                <p className="detail-summary">{selectedEvent.message ?? "No event summary available."}</p>
                <div className="detail-grid detail-grid--summary">
                  <div>
                    <span className="detail-label">
                      Connection flow
                    </span>
                    <strong>{formatFlow(selectedEvent.source_ip, selectedEvent.dest_ip)}</strong>
                  </div>
                  <div>
                    <span className="detail-label">Raw payload</span>
                    <strong>{selectedEvent.raw_log.trim().startsWith("{") ? "JSON payload" : "Text log line"}</strong>
                  </div>
                </div>
                <pre className="code-surface code-surface--compact">{selectedEvent.raw_log}</pre>
              </div>
            ) : (
              <p className="table-message">Select an event row to inspect normalized details.</p>
            )}
          </DataPanel>
        </div>
      ) : null}
    </div>
  );
}
