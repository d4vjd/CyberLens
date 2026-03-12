// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

const tokenOverrides: Record<string, string> = {
  api: "API",
  dns: "DNS",
  ftp: "FTP",
  ip: "IP",
  ir: "IR",
  json: "JSON",
  mitre: "MITRE",
  mttd: "MTTD",
  mttr: "MTTR",
  smb: "SMB",
  soc: "SOC",
  ssh: "SSH",
  tcp: "TCP",
  udp: "UDP",
  vpn: "VPN",
};

export function humanizeIdentifier(value: string) {
  return value
    .split(/[_\-\s]+/)
    .filter(Boolean)
    .map((token) => tokenOverrides[token.toLowerCase()] ?? `${token[0]?.toUpperCase() ?? ""}${token.slice(1)}`)
    .join(" ");
}

export function humanizeCompactStatus(value: string) {
  return humanizeIdentifier(value).replace(/\bAnd\b/g, "and");
}

export function formatNullable(value: string | number | null | undefined, fallback = "Not available") {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }
  return String(value);
}

export function formatDateTime(value: string) {
  return new Date(value).toLocaleString([], {
    dateStyle: "short",
    timeStyle: "short",
  });
}

export function formatFlow(source: string | null, destination: string | null) {
  return `${source ?? "Unknown source"} \u2192 ${destination ?? "Unknown destination"}`;
}

export function formatTechniqueMapping(tactic: string | null, techniqueId: string | null) {
  if (!tactic && !techniqueId) {
    return "No ATT&CK mapping";
  }

  if (!tactic) {
    return techniqueId ?? "No ATT&CK mapping";
  }

  if (!techniqueId) {
    return humanizeIdentifier(tactic);
  }

  return `${humanizeIdentifier(tactic)} / ${techniqueId}`;
}

export function formatCountLabel(value: number, singular: string, plural = `${singular}s`) {
  return `${value.toLocaleString()} ${value === 1 ? singular : plural}`;
}
