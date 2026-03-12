// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";

import { useDemoStore } from "../../app/store/demoStore";
import { DataPanel } from "../../shared/components/DataPanel";
import { PageIntro } from "../../shared/components/PageIntro";
import { SearchInput } from "../../shared/components/SearchInput";
import { StatusBadge } from "../../shared/components/StatusBadge";
import { useDebounce } from "../../shared/hooks/useDebounce";
import type { RuleRecord } from "../../shared/types";
import { deleteJson, fetchJson, postJson } from "../../shared/utils/api";
import { getSyntheticRules } from "../../shared/utils/mockData";

type ApiRule = {
  rule_id: string;
  title: string;
  description: string | null;
  severity: RuleRecord["severity"];
  rule_type: RuleRecord["type"];
  mitre_tactic: string | null;
  mitre_technique_id: string | null;
  enabled: boolean;
  historical_matches: number;
  last_triggered_at: string | null;
};

type RuleMutationResponse = {
  rule_id: string;
  title: string;
  file_path: string;
  enabled: boolean;
  message: string;
};

type RuleHistoricalTestResponse = {
  rule_id: string;
  title: string;
  evaluated_events: number;
  generated_alerts: number;
  sample_event_ids: number[];
  sample_matches: Array<Record<string, unknown>>;
};

async function fetchLiveRules(): Promise<RuleRecord[]> {
  const rules = await fetchJson<ApiRule[]>("/rules");
  return rules.map((rule) => ({
    id: rule.rule_id,
    title: rule.title,
    description: rule.description ?? "Loaded from the detection engine rule catalog.",
    severity: rule.severity,
    type: rule.rule_type,
    enabled: rule.enabled,
    mitre_tactic: rule.mitre_tactic ?? "unmapped",
    mitre_technique_id: rule.mitre_technique_id ?? "n/a",
    historical_matches: rule.historical_matches,
    last_triggered_at: rule.last_triggered_at,
    yaml: `id: ${rule.rule_id}
title: ${rule.title}
severity: ${rule.severity}
type: ${rule.rule_type}
mitre:
  tactic: ${rule.mitre_tactic ?? "unmapped"}
  technique_id: ${rule.mitre_technique_id ?? "n/a"}`,
  }));
}

export function RulesPage() {
  const queryClient = useQueryClient();
  const dataSource = useDemoStore((state) => state.dataSource);
  const [search, setSearch] = useState("");
  const [selectedRule, setSelectedRule] = useState<RuleRecord | null>(null);
  const [preferredRuleId, setPreferredRuleId] = useState<string | null>(null);
  const [editableYaml, setEditableYaml] = useState("");
  const debouncedSearch = useDebounce(search, 250);
  const [reloadMessage, setReloadMessage] = useState("");
  const [testResult, setTestResult] = useState<RuleHistoricalTestResponse | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["rules", dataSource],
    queryFn: () =>
      dataSource === "synthetic" ? Promise.resolve(getSyntheticRules()) : fetchLiveRules(),
  });

  const reloadRulesMutation = useMutation({
    mutationFn: () => postJson<{ loaded_count: number; loaded_rule_ids: string[] }>("/detection/rules/reload"),
    onSuccess: async (payload) => {
      setReloadMessage(`Reloaded ${payload.loaded_count} rule definitions from disk.`);
      await queryClient.invalidateQueries({ queryKey: ["rules"] });
    },
  });

  const saveRuleMutation = useMutation({
    mutationFn: () => postJson<RuleMutationResponse>("/rules", { yaml: editableYaml }),
    onSuccess: async (payload) => {
      setPreferredRuleId(payload.rule_id);
      setReloadMessage(payload.message);
      await queryClient.invalidateQueries({ queryKey: ["rules"] });
    },
  });

  const testRuleMutation = useMutation({
    mutationFn: () =>
      postJson<RuleHistoricalTestResponse>("/rules/test", {
        yaml: editableYaml,
        limit: 500,
      }),
    onSuccess: (payload) => {
      setTestResult(payload);
      setReloadMessage(
        `Historical test completed across ${payload.evaluated_events} recent events and produced ${payload.generated_alerts} alert candidates.`,
      );
    },
  });

  const retireRuleMutation = useMutation({
    mutationFn: (ruleId: string) => deleteJson<RuleMutationResponse>(`/rules/${ruleId}`),
    onSuccess: async (payload) => {
      setPreferredRuleId(null);
      setSelectedRule(null);
      setEditableYaml("");
      setTestResult(null);
      setReloadMessage(payload.message);
      await queryClient.invalidateQueries({ queryKey: ["rules"] });
    },
  });

  const filteredRules = useMemo(() => {
    const rules = data ?? [];
    if (!debouncedSearch) {
      return rules;
    }

    const needle = debouncedSearch.toLowerCase();
    return rules.filter((rule) =>
      [rule.id, rule.title, rule.mitre_tactic, rule.mitre_technique_id]
        .join(" ")
        .toLowerCase()
        .includes(needle),
    );
  }, [data, debouncedSearch]);

  useEffect(() => {
    if (!filteredRules.length) {
      setSelectedRule(null);
      return;
    }

    setSelectedRule((current) => {
      const nextSelection =
        (preferredRuleId ? filteredRules.find((rule) => rule.id === preferredRuleId) : null) ??
        filteredRules.find((rule) => rule.id === current?.id) ??
        filteredRules[0];
      return nextSelection;
    });
  }, [filteredRules, preferredRuleId]);

  useEffect(() => {
    setEditableYaml(selectedRule?.yaml ?? "");
    setTestResult(null);
  }, [selectedRule?.id]);

  return (
    <div className="page-grid">
      <PageIntro
        eyebrow="Rules"
        title="Detection authoring"
        description="Browse enabled rules, inspect their YAML definitions, and in live mode save or test rules against recent telemetry before promoting them."
        actions={
          <StatusBadge
            label={dataSource === "synthetic" ? "Synthetic rule lab" : `${filteredRules.length} live rules`}
            tone={dataSource === "synthetic" ? "connected" : "low"}
          />
        }
      />

      <DataPanel subtitle="Search by rule id, title, tactic, or technique" title="Rule catalog">
        <div className="filter-grid filter-grid--compact">
          <SearchInput onChange={setSearch} placeholder="Search rule id, title, or ATT&CK mapping" value={search} />
          {dataSource === "live" ? (
            <button
              className="ghost-button"
              disabled={reloadRulesMutation.isPending}
              onClick={() => reloadRulesMutation.mutate()}
              type="button"
            >
              {reloadRulesMutation.isPending ? "Reloading…" : "Reload from disk"}
            </button>
          ) : null}
        </div>
      </DataPanel>

      {reloadMessage ? (
        <DataPanel subtitle="Latest content sync" title="Rule loader">
          <p className="table-message">{reloadMessage}</p>
        </DataPanel>
      ) : null}

      {isLoading ? <p className="table-message">Loading rule catalog…</p> : null}
      {isError ? <p className="table-message">Failed to load detection rules.</p> : null}

      {!isLoading && !isError ? (
        <div className="content-grid content-grid--wide">
          <DataPanel subtitle="Enabled detection content" title="Rules">
            <div className="rule-list">
              {filteredRules.map((rule) => (
                <button
                  className={`rule-list__item ${selectedRule?.id === rule.id ? "rule-list__item--active" : ""}`}
                  key={rule.id}
                  onClick={() => setSelectedRule(rule)}
                  type="button"
                >
                  <div>
                    <strong>{rule.title}</strong>
                    <p>
                      {rule.id} · {rule.mitre_tactic} / {rule.mitre_technique_id}
                    </p>
                  </div>
                  <div className="panel-badge-row">
                    <StatusBadge label={rule.severity} tone={rule.severity} />
                    <StatusBadge label={rule.type} tone="neutral" />
                  </div>
                </button>
              ))}
            </div>
          </DataPanel>

          <DataPanel subtitle="YAML-first editor preview" title={selectedRule ? selectedRule.title : "Rule detail"}>
            {selectedRule ? (
              <div className="detail-stack">
                <div className="panel-badge-row">
                  <StatusBadge label={selectedRule.severity} tone={selectedRule.severity} />
                  <StatusBadge label={selectedRule.type} tone="neutral" />
                  <StatusBadge
                    label={selectedRule.enabled ? "enabled" : "disabled"}
                    tone={selectedRule.enabled ? "connected" : "offline"}
                  />
                </div>
                <p className="detail-summary">{selectedRule.description}</p>
                <div className="detail-grid">
                  <div>
                    <span className="detail-label">Technique</span>
                    <strong>{selectedRule.mitre_technique_id}</strong>
                  </div>
                  <div>
                    <span className="detail-label">Tactic</span>
                    <strong>{selectedRule.mitre_tactic}</strong>
                  </div>
                  <div>
                    <span className="detail-label">Historical matches</span>
                    <strong>{selectedRule.historical_matches}</strong>
                  </div>
                  <div>
                    <span className="detail-label">Last triggered</span>
                    <strong>
                      {selectedRule.last_triggered_at
                        ? new Date(selectedRule.last_triggered_at).toLocaleString()
                        : dataSource === "synthetic"
                          ? "Not exercised"
                          : "Not triggered yet"}
                    </strong>
                  </div>
                </div>

                {dataSource === "live" ? (
                  <>
                    <div className="action-row">
                      <button
                        className="primary-button"
                        disabled={saveRuleMutation.isPending || !editableYaml.trim()}
                        onClick={() => saveRuleMutation.mutate()}
                        type="button"
                      >
                        {saveRuleMutation.isPending ? "Saving…" : "Save YAML"}
                      </button>
                      <button
                        className="ghost-button"
                        disabled={testRuleMutation.isPending || !editableYaml.trim()}
                        onClick={() => testRuleMutation.mutate()}
                        type="button"
                      >
                        {testRuleMutation.isPending ? "Testing…" : "Test recent events"}
                      </button>
                      <button
                        className="ghost-button"
                        disabled={retireRuleMutation.isPending}
                        onClick={() => {
                          if (window.confirm(`Retire rule ${selectedRule.id} from the active catalog?`)) {
                            retireRuleMutation.mutate(selectedRule.id);
                          }
                        }}
                        type="button"
                      >
                        {retireRuleMutation.isPending ? "Retiring…" : "Retire rule"}
                      </button>
                    </div>
                    <textarea
                      className="code-editor"
                      onChange={(event) => setEditableYaml(event.target.value)}
                      spellCheck={false}
                      value={editableYaml}
                    />
                  </>
                ) : (
                  <pre className="code-surface">{selectedRule.yaml}</pre>
                )}

                {testResult ? (
                  <div className="result-grid">
                    <div>
                      <span className="detail-label">Evaluated events</span>
                      <strong>{testResult.evaluated_events}</strong>
                    </div>
                    <div>
                      <span className="detail-label">Generated alerts</span>
                      <strong>{testResult.generated_alerts}</strong>
                    </div>
                    <div>
                      <span className="detail-label">Sample event ids</span>
                      <strong>{testResult.sample_event_ids.join(", ") || "No matches"}</strong>
                    </div>
                    <div>
                      <span className="detail-label">Sample match payloads</span>
                      <strong>{testResult.sample_matches.length}</strong>
                    </div>
                  </div>
                ) : null}
              </div>
            ) : (
              <p className="table-message">No rule matched the current search.</p>
            )}
          </DataPanel>
        </div>
      ) : null}
    </div>
  );
}