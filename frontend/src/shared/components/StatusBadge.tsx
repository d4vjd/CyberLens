// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

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
};

export function StatusBadge({ label, tone = "neutral" }: StatusBadgeProps) {
  return <span className={`status-badge status-badge--${tone}`}>{label}</span>;
}