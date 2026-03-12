// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import { Tooltip } from "./Tooltip";

type MetricTone = "critical" | "high" | "medium" | "low" | "neutral";

type MetricCardProps = {
  label: string;
  value: string;
  delta: string;
  tone?: MetricTone;
  tooltip?: string;
};

export function MetricCard({ label, value, delta, tone = "neutral", tooltip }: MetricCardProps) {
  const card = (
    <article className={`metric-card metric-card--${tone}`}>
      <p>{label}</p>
      <strong>{value}</strong>
      <span>{delta}</span>
    </article>
  );

  if (!tooltip) {
    return card;
  }

  return (
    <Tooltip block content={tooltip}>
      {card}
    </Tooltip>
  );
}
