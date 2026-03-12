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
        title="Normalized event stream"
        description="Filter the raw intake, inspect normalized fields, and switch to synthetic telemetry whenever you need a fully populated walkthrough."
        actions={
          <div className="panel-badge-row">
            <StatusBadge
              label={dataSource === "synthetic" ? "Synthetic feed" : liveStream ? "Live feed enabled" : "Live feed paused"}
              tone={dataSource === "synthetic" ? "connected" : liveStream ? "low" : "neutral"}
            />
            <StatusBadge label={`${data?.total ?? 0} indexed`} tone="neutral" />
          </div>
        }
      />

      <DataPanel subtitle="Filter by search term, type, source, or severity" title="Search controls">
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
            value={eventType}
          />
          <input
            className="filter-input"
            onChange={(event) => setSourceSystem(event.target.value)}
            placeholder="Source system"
            value={sourceSystem}
          />
          <select className="filter-input" onChange={(event) => setSeverity(event.target.value)} value={severity}>
            <option value="">All severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
      </DataPanel>

      {isLoading ? <p className="table-message">Loading event stream…</p> : null}
      {isError ? <p className="table-message">Failed to load events from the selected data source.</p> : null}

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
                  render: (event) => new Date(event.timestamp).toLocaleString(),
                },
                {
                  header: "Type",
                  render: (event) => event.event_type,
                },
                {
                  header: "Source",
                  render: (event) => event.source_system,
                },
                {
                  header: "Path",
                  render: (event) => `${event.source_ip ?? "n/a"} → ${event.dest_ip ?? "n/a"}`,
                },
                {
                  header: "Action",
                  render: (event) => event.action ?? "n/a",
                },
                {
                  header: "Severity",
                  render: (event) => <StatusBadge label={event.severity} tone={event.severity} />,
                },
              ]}
              emptyMessage="No events matched the current filters."
              items={data.items}
              onRowClick={setSelectedEvent}
              rowKey={(event) => event.id}
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
            title={selectedEvent ? `${selectedEvent.event_type} · #${selectedEvent.id}` : "Event detail"}
          >
            {selectedEvent ? (
              <div className="detail-stack">
                <div className="detail-grid">
                  <div>
                    <span className="detail-label">Host</span>
                    <strong>{selectedEvent.hostname ?? "n/a"}</strong>
                  </div>
                  <div>
                    <span className="detail-label">User</span>
                    <strong>{selectedEvent.username ?? "n/a"}</strong>
                  </div>
                  <div>
                    <span className="detail-label">Protocol</span>
                    <strong>{selectedEvent.protocol ?? "n/a"}</strong>
                  </div>
                  <div>
                    <span className="detail-label">Port</span>
                    <strong>{selectedEvent.dest_port ?? "n/a"}</strong>
                  </div>
                </div>
                <p className="detail-summary">{selectedEvent.message ?? "No event summary available."}</p>
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