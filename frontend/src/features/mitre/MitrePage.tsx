// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { useDemoStore } from "../../app/store/demoStore";
import { DataPanel } from "../../shared/components/DataPanel";
import { PageIntro } from "../../shared/components/PageIntro";
import { StatusBadge } from "../../shared/components/StatusBadge";
import type {
  MitreMatrixResponse,
  MitreTechnique,
  MitreTechniqueDetail,
} from "../../shared/types";
import { fetchJson } from "../../shared/utils/api";
import { getSyntheticMatrix, getSyntheticTechniqueDetail } from "../../shared/utils/mockData";

function techniqueTone(technique: MitreTechnique): "neutral" | "low" | "medium" | "high" | "critical" {
  if (technique.alert_count >= 3) {
    return "critical";
  }
  if (technique.alert_count >= 2) {
    return "high";
  }
  if (technique.alert_count >= 1) {
    return "medium";
  }
  if (technique.rule_count >= 1) {
    return "low";
  }
  return "neutral";
}

export function MitrePage() {
  const dataSource = useDemoStore((state) => state.dataSource);
  const [selectedTechniqueId, setSelectedTechniqueId] = useState<string | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["mitre-matrix", dataSource],
    queryFn: () =>
      dataSource === "synthetic"
        ? Promise.resolve(getSyntheticMatrix())
        : fetchJson<MitreMatrixResponse>("/mitre/matrix"),
  });

  useEffect(() => {
    if (!data?.tactics.length) {
      setSelectedTechniqueId(null);
      return;
    }

    const firstTechnique = data.tactics[0]?.techniques[0];
    setSelectedTechniqueId((current) => current ?? firstTechnique?.technique_id ?? null);
  }, [data]);

  const { data: detail } = useQuery({
    enabled: !!selectedTechniqueId,
    queryKey: ["mitre-technique", dataSource, selectedTechniqueId],
    queryFn: () => {
      if (!selectedTechniqueId) {
        throw new Error("Technique id is required");
      }
      return dataSource === "synthetic"
        ? Promise.resolve(getSyntheticTechniqueDetail(selectedTechniqueId))
        : fetchJson<MitreTechniqueDetail>(`/mitre/techniques/${selectedTechniqueId}`);
    },
  });

  return (
    <div className="page-grid">
      <PageIntro
        eyebrow="MITRE ATT&CK"
        title="Coverage matrix"
        description="Inspect tactic coverage, select any technique for rule and alert detail, and use synthetic mode to fill the matrix for portfolio screenshots."
        actions={
          <StatusBadge
            label={dataSource === "synthetic" ? "Synthetic coverage" : `${data?.tactics.length ?? 0} tactics loaded`}
            tone={dataSource === "synthetic" ? "connected" : "low"}
          />
        }
      />

      {isLoading ? <p className="table-message">Loading ATT&CK matrix…</p> : null}
      {isError ? <p className="table-message">Failed to load ATT&CK matrix.</p> : null}

      {!isLoading && !isError && data ? (
        <div className="content-grid content-grid--wide">
          <DataPanel subtitle="Select a technique cell to inspect coverage" title="ATT&CK matrix">
            <section className="mitre-matrix mitre-matrix--scroll">
              {data.tactics.map((column) => (
                <div className="mitre-column-panel" key={column.tactic}>
                  <div className="mitre-column-panel__header">
                    <strong>{column.tactic}</strong>
                    <span>{column.techniques.length} techniques</span>
                  </div>
                  <div className="mitre-column">
                    {column.techniques.map((technique) => (
                      <button
                        className={`mitre-technique mitre-technique--${techniqueTone(technique)} ${
                          selectedTechniqueId === technique.technique_id ? "mitre-technique--active" : ""
                        }`}
                        key={technique.technique_id}
                        onClick={() => setSelectedTechniqueId(technique.technique_id)}
                        type="button"
                      >
                        <div className="mitre-technique__header">
                          <strong>{technique.technique_id}</strong>
                          <StatusBadge
                            label={`${technique.alert_count} alerts`}
                            tone={techniqueTone(technique)}
                          />
                        </div>
                        <h5>{technique.name}</h5>
                        <p>{technique.description}</p>
                        <div className="mitre-technique__meta">
                          <span>{technique.rule_count} rules</span>
                          <span>
                            {technique.last_alert_at
                              ? new Date(technique.last_alert_at).toLocaleString()
                              : "No alert yet"}
                          </span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </section>
          </DataPanel>

          <DataPanel
            subtitle="Technique drill-down"
            title={detail ? `${detail.technique_id} · ${detail.name}` : "Technique detail"}
          >
            {detail ? (
              <div className="detail-stack">
                <div className="panel-badge-row">
                  <StatusBadge label={detail.tactic} tone="neutral" />
                  <StatusBadge label={`${detail.rule_count} rules`} tone="low" />
                  <StatusBadge
                    label={`${detail.alert_count} alerts`}
                    tone={detail.alert_count ? "high" : "neutral"}
                  />
                </div>
                <p className="detail-summary">{detail.description}</p>
                <div className="detail-grid">
                  <div>
                    <span className="detail-label">Last alert</span>
                    <strong>
                      {detail.last_alert_at
                        ? new Date(detail.last_alert_at).toLocaleString()
                        : "No detections yet"}
                    </strong>
                  </div>
                  <div>
                    <span className="detail-label">Mapped rules</span>
                    <strong>{detail.rule_ids.length}</strong>
                  </div>
                </div>
                <div className="pill-list">
                  {detail.rule_ids.map((ruleId) => (
                    <span className="pill-chip" key={ruleId}>
                      {ruleId}
                    </span>
                  ))}
                </div>
              </div>
            ) : (
              <p className="table-message">Select a technique cell to inspect rule coverage.</p>
            )}
          </DataPanel>
        </div>
      ) : null}
    </div>
  );
}