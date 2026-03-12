// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

/**
 * Design-token reference for any component that needs programmatic
 * access to the active palette (e.g. Recharts tooltip styles).
 *
 * The canonical source of truth is globals.css — these values must
 * stay in sync with the CSS custom properties defined there.
 */
export const themeTokens = {
  night: {
    bg: "#0c0c0e",
    bgElevated: "#141417",
    bgPanel: "#18181b",
    border: "rgba(255, 255, 255, 0.07)",
    text: "#ececef",
    textMuted: "#a0a0ab",
    textFaint: "#636370",
    accent: "#3dd8c5",
    accentStrong: "#f97316",
    gridStroke: "rgba(255, 255, 255, 0.06)",
    axisStroke: "rgba(255, 255, 255, 0.25)",
  },
  dawn: {
    bg: "#f4f4f5",
    bgElevated: "#ffffff",
    bgPanel: "#ffffff",
    border: "rgba(0, 0, 0, 0.08)",
    text: "#18181b",
    textMuted: "#52525b",
    textFaint: "#a1a1aa",
    accent: "#0d9488",
    accentStrong: "#ea580c",
    gridStroke: "rgba(0, 0, 0, 0.06)",
    axisStroke: "rgba(0, 0, 0, 0.25)",
  },
} as const;

/** Severity → hex color map shared across charts and components. */
export const severityColors: Record<string, string> = {
  critical: "#ef4444",
  high: "#f97316",
  medium: "#eab308",
  low: "#22c55e",
  neutral: "#71717a",
};