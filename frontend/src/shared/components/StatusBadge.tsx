// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import { Tooltip } from "./Tooltip";

type StatusTone =
  | "critical"
  | "high"
  | "medium"
  | "low"
  | "neutral"
  | "connected"
  | "offline";

type StatusBadgeProps = {
  label: string;
  tone?: StatusTone;
  tooltip?: string;
};

export function StatusBadge({ label, tone = "neutral", tooltip }: StatusBadgeProps) {
  const badge = (
    <span className={`status-badge status-badge--${tone}`}>
      <span className="status-badge__dot" style={{ background: "currentColor" }} />
      {label}
    </span>
  );

  if (!tooltip) {
    return badge;
  }

  return <Tooltip content={tooltip}>{badge}</Tooltip>;
}
