// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { useDemoStore } from "../../app/store/demoStore";
import { DataPanel } from "../../shared/components/DataPanel";
import { PageIntro } from "../../shared/components/PageIntro";
import { StatusBadge } from "../../shared/components/StatusBadge";
import type { CaseDetailApi, CaseListResponseApi, CaseRecord } from "../../shared/types";
import { fetchJson, patchJson, postJson } from "../../shared/utils/api";
import { getSyntheticCases } from "../../shared/utils/mockData";

const tabs = ["overview", "timeline", "evidence", "playbook"] as const;

async function fetchLiveCases() {
  return fetchJson<CaseListResponseApi>("/incidents");
}

async function fetchLiveCaseDetail(caseUid: string) {
  return fetchJson<CaseDetailApi>(`/incidents/${caseUid}`);
}

export function CasesPage() {
  const queryClient = useQueryClient();
  const dataSource = useDemoStore((state) => state.dataSource);
  const setDataSource = useDemoStore((state) => state.setDataSource);
  const syntheticCases = getSyntheticCases();
  const [selectedCaseId, setSelectedCaseId] = useState(syntheticCases[0]?.id ?? "");
  const [activeTab, setActiveTab] = useState<(typeof tabs)[number]>("overview");
  const [actionMessage, setActionMessage] = useState("");

  const liveCasesQuery = useQuery({
    queryKey: ["cases", "live"],
    queryFn: fetchLiveCases,
    enabled: dataSource === "live",
  });

  const liveCases = liveCasesQuery.data?.items ?? [];
  const liveSelectedCaseUid = dataSource === "live" ? selectedCaseId : "";
  const liveCaseDetailQuery = useQuery({
    queryKey: ["case-detail", liveSelectedCaseUid],
    queryFn: () => fetchLiveCaseDetail(liveSelectedCaseUid),
    enabled: dataSource === "live" && Boolean(liveSelectedCaseUid),
  });

  useEffect(() => {
    if (dataSource === "synthetic") {
      if (!syntheticCases.some((item) => item.id === selectedCaseId)) {
        setSelectedCaseId(syntheticCases[0]?.id ?? "");
      }
      return;
    }

    if (!liveCases.some((item) => item.case_uid === selectedCaseId)) {
      setSelectedCaseId(liveCases[0]?.case_uid ?? "");
    }
  }, [dataSource, liveCases, selectedCaseId, syntheticCases]);

  const runPlaybookMutation = useMutation({
    mutationFn: (caseUid: string) =>
      postJson(`/incidents/${caseUid}/playbook/run`, {
        actor: "ahassan",
      }),
    onSuccess: async (_, caseUid) => {
      setActionMessage("Playbook executed and timeline updated.");
      await queryClient.invalidateQueries({ queryKey: ["case-detail", caseUid] });
      await queryClient.invalidateQueries({ queryKey: ["cases", "live"] });
    },
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ caseUid, status }: { caseUid: string; status: string }) =>
      patchJson(`/incidents/${caseUid}`, {
        actor: "ahassan",
        status,
      }),
    onSuccess: async (_, variables) => {
      setActionMessage(`Case moved to ${variables.status}.`);
      await queryClient.invalidateQueries({ queryKey: ["case-detail", variables.caseUid] });
      await queryClient.invalidateQueries({ queryKey: ["cases", "live"] });
    },
  });

  const selectedSyntheticCase = syntheticCases.find((item) => item.id === selectedCaseId) ?? syntheticCases[0];
  const selectedLiveCase = liveCaseDetailQuery.data;

  return (
    <div className="page-grid">
      <PageIntro
        eyebrow="Cases"
        title="Incident response workspace"
        description="Track escalations, playbooks, evidence, and response actions. Synthetic mode remains available for densely staged screenshots, while live mode now consumes the incident API."
        actions={
          <StatusBadge
            label={dataSource === "synthetic" ? "Synthetic workflow active" : `${liveCases.length} live cases`}
            tone={dataSource === "synthetic" ? "connected" : "medium"}
          />
        }
      />

      {dataSource === "live" && !liveCases.length && !liveCasesQuery.isLoading ? (
        <DataPanel
          actions={
            <button className="primary-button" onClick={() => setDataSource("synthetic")} type="button">
              Switch to synthetic cases
            </button>
          }
          subtitle="The live case API is active, but your environment does not have seeded or escalated cases yet."
          title="No live cases available"
        >
          <p className="table-message">
            Seed demo data from Settings or escalate an alert from the Alerts page to populate the live incident queue.
          </p>
        </DataPanel>
      ) : null}

      {actionMessage ? (
        <DataPanel subtitle="Most recent workflow action" title="Operator update">
          <p className="table-message">{actionMessage}</p>
        </DataPanel>
      ) : null}

      <div className="content-grid content-grid--wide">
        <DataPanel subtitle="Open and recent cases" title="Case list">
          <div className="rule-list">
            {dataSource === "synthetic"
              ? syntheticCases.map((item) => (
                  <button
                    className={`rule-list__item ${selectedCaseId === item.id ? "rule-list__item--active" : ""}`}
                    key={item.id}
                    onClick={() => setSelectedCaseId(item.id)}
                    type="button"
                  >
                    <div>
                      <strong>{item.title}</strong>
                      <p>
                        {item.id} · {item.assigned_to}
                      </p>
                    </div>
                    <div className="panel-badge-row">
                      <StatusBadge label={item.status} tone="neutral" />
                      <StatusBadge label={item.severity} tone={item.severity} />
                    </div>
                  </button>
                ))
              : liveCases.map((item) => (
                  <button
                    className={`rule-list__item ${selectedCaseId === item.case_uid ? "rule-list__item--active" : ""}`}
                    key={item.case_uid}
                    onClick={() => setSelectedCaseId(item.case_uid)}
                    type="button"
                  >
                    <div>
                      <strong>{item.title}</strong>
                      <p>
                        {item.case_uid} · {item.assigned_to ?? "Unassigned"}
                      </p>
                    </div>
                    <div className="panel-badge-row">
                      <StatusBadge label={item.status} tone="neutral" />
                      <StatusBadge label={item.severity} tone={item.severity} />
                    </div>
                  </button>
                ))}
          </div>
        </DataPanel>

        <DataPanel subtitle="Overview, timeline, evidence, and playbook tabs" title={selectedLiveCase?.title ?? selectedSyntheticCase?.title ?? "Case detail"}>
          <div className="detail-stack">
            <div className="tab-strip">
              {tabs.map((tab) => (
                <button
                  className={tab === activeTab ? "tab-strip__tab tab-strip__tab--active" : "tab-strip__tab"}
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  type="button"
                >
                  {tab}
                </button>
              ))}
            </div>

            {dataSource === "synthetic" ? (
              <SyntheticCaseDetail activeTab={activeTab} selectedCase={selectedSyntheticCase} />
            ) : liveCaseDetailQuery.isLoading ? (
              <p className="table-message">Loading case detail…</p>
            ) : selectedLiveCase ? (
              <>
                {activeTab === "overview" ? (
                  <>
                    <div className="panel-badge-row">
                      <StatusBadge label={selectedLiveCase.severity} tone={selectedLiveCase.severity} />
                      <StatusBadge label={selectedLiveCase.status} tone="neutral" />
                      <StatusBadge
                        label={selectedLiveCase.playbook_id ?? "no playbook"}
                        tone={selectedLiveCase.playbook_id ? "medium" : "neutral"}
                      />
                    </div>
                    <div className="detail-grid">
                      <div>
                        <span className="detail-label">Priority</span>
                        <strong>P{selectedLiveCase.priority}</strong>
                      </div>
                      <div>
                        <span className="detail-label">Assigned</span>
                        <strong>{selectedLiveCase.assigned_to ?? "Unassigned"}</strong>
                      </div>
                      <div>
                        <span className="detail-label">SLA due</span>
                        <strong>
                          {selectedLiveCase.sla_due_at ? new Date(selectedLiveCase.sla_due_at).toLocaleString() : "n/a"}
                        </strong>
                      </div>
                      <div>
                        <span className="detail-label">Linked alerts</span>
                        <strong>{selectedLiveCase.alerts.length}</strong>
                      </div>
                    </div>
                    <p className="detail-summary">
                      {selectedLiveCase.description ?? "No case summary has been recorded yet."}
                    </p>
                    <div className="pill-list">
                      {selectedLiveCase.alerts.map((alert) => (
                        <span className="pill-chip" key={alert.alert_uid}>
                          {alert.alert_uid}
                        </span>
                      ))}
                    </div>
                    <div className="panel-badge-row">
                      <button
                        className="primary-button"
                        disabled={runPlaybookMutation.isPending}
                        onClick={() => runPlaybookMutation.mutate(selectedLiveCase.case_uid)}
                        type="button"
                      >
                        {runPlaybookMutation.isPending ? "Running playbook…" : "Run playbook"}
                      </button>
                      <button
                        className="ghost-button"
                        disabled={updateStatusMutation.isPending}
                        onClick={() =>
                          updateStatusMutation.mutate({ caseUid: selectedLiveCase.case_uid, status: "in_progress" })
                        }
                        type="button"
                      >
                        Mark in progress
                      </button>
                      <button
                        className="ghost-button"
                        disabled={updateStatusMutation.isPending}
                        onClick={() =>
                          updateStatusMutation.mutate({ caseUid: selectedLiveCase.case_uid, status: "resolved" })
                        }
                        type="button"
                      >
                        Resolve case
                      </button>
                    </div>
                  </>
                ) : null}

                {activeTab === "timeline" ? (
                  <div className="timeline-preview">
                    {selectedLiveCase.timeline.map((entry) => (
                      <div className="timeline-preview__item" key={entry.id}>
                        <span />
                        <div>
                          <strong>{entry.summary}</strong>
                          <p>
                            {new Date(entry.created_at).toLocaleString()} · {entry.actor} · {entry.event_type}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : null}

                {activeTab === "evidence" ? (
                  selectedLiveCase.evidence.length ? (
                    <div className="watchlist-grid">
                      {selectedLiveCase.evidence.map((item) => (
                        <article className="watchlist-card" key={item.id}>
                          <span>{item.content_type}</span>
                          <strong>{item.filename}</strong>
                          <p>{Math.round(item.file_size / 1024)} KB</p>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <p className="table-message">No evidence has been attached to this case yet.</p>
                  )
                ) : null}

                {activeTab === "playbook" ? (
                  selectedLiveCase.response_actions.length ? (
                    <div className="timeline-preview">
                      {selectedLiveCase.response_actions.map((action) => (
                        <div className="timeline-preview__item" key={action.id}>
                          <span />
                          <div>
                            <strong>{action.action_type}</strong>
                            <p>
                              {action.target} · {action.status} · {new Date(action.created_at).toLocaleString()}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="table-message">Run the playbook to populate response actions for this case.</p>
                  )
                ) : null}
              </>
            ) : (
              <p className="table-message">Select a case from the list to inspect it.</p>
            )}
          </div>
        </DataPanel>
      </div>
    </div>
  );
}

function SyntheticCaseDetail({
  activeTab,
  selectedCase,
}: {
  activeTab: (typeof tabs)[number];
  selectedCase: CaseRecord | undefined;
}) {
  if (!selectedCase) {
    return <p className="table-message">No case selected.</p>;
  }

  return (
    <>
      {activeTab === "overview" ? (
        <>
          <div className="detail-grid">
            <div>
              <span className="detail-label">Severity</span>
              <strong>{selectedCase.severity}</strong>
            </div>
            <div>
              <span className="detail-label">Priority</span>
              <strong>P{selectedCase.priority}</strong>
            </div>
            <div>
              <span className="detail-label">Assigned</span>
              <strong>{selectedCase.assigned_to}</strong>
            </div>
            <div>
              <span className="detail-label">SLA due</span>
              <strong>{new Date(selectedCase.sla_due_at).toLocaleString()}</strong>
            </div>
          </div>
          <p className="detail-summary">{selectedCase.summary}</p>
          <div className="pill-list">
            {selectedCase.alerts.map((alertId) => (
              <span className="pill-chip" key={alertId}>
                {alertId}
              </span>
            ))}
          </div>
        </>
      ) : null}

      {activeTab === "timeline" ? (
        <div className="timeline-preview">
          {selectedCase.timeline.map((entry) => (
            <div className="timeline-preview__item" key={`${entry.at}-${entry.summary}`}>
              <span />
              <div>
                <strong>{entry.summary}</strong>
                <p>
                  {new Date(entry.at).toLocaleString()} · {entry.actor} · {entry.kind}
                </p>
              </div>
            </div>
          ))}
        </div>
      ) : null}

      {activeTab === "evidence" ? (
        <div className="watchlist-grid">
          {Array.from({ length: selectedCase.evidence_count }, (_, index) => (
            <article className="watchlist-card" key={index}>
              <span>Evidence item {index + 1}</span>
              <strong>artifact-{index + 1}.json</strong>
              <StatusBadge label="collected" tone="low" />
            </article>
          ))}
        </div>
      ) : null}

      {activeTab === "playbook" ? (
        <div className="timeline-preview">
          <div className="timeline-preview__item">
            <span />
            <div>
              <strong>Validate scope and impacted identities</strong>
              <p>Pull correlated alerts, endpoint context, and authentication trail.</p>
            </div>
          </div>
          <div className="timeline-preview__item">
            <span />
            <div>
              <strong>Contain and record response action</strong>
              <p>Simulate host isolation or account disablement with timeline attribution.</p>
            </div>
          </div>
          <div className="timeline-preview__item">
            <span />
            <div>
              <strong>Collect evidence and resolution notes</strong>
              <p>Attach artifacts, note findings, and close or escalate with full audit trail.</p>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}