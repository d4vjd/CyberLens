// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

export const apiBaseUrl = "/api/v1";

export function buildQuery(params: Record<string, string | number | undefined | null>) {
  const query = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }
    query.set(key, String(value));
  });

  const serialized = query.toString();
  return serialized ? `?${serialized}` : "";
}

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, init);
  if (!response.ok) {
    throw new Error(`Request failed for ${path}`);
  }
  return response.json() as Promise<T>;
}

export async function sendJson<TResponse>(
  path: string,
  method: "POST" | "PATCH" | "DELETE",
  body?: unknown,
): Promise<TResponse> {
  return fetchJson<TResponse>(path, {
    method,
    headers: {
      "Content-Type": "application/json",
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export function postJson<TResponse>(path: string, body?: unknown): Promise<TResponse> {
  return sendJson<TResponse>(path, "POST", body);
}

export function patchJson<TResponse>(path: string, body?: unknown): Promise<TResponse> {
  return sendJson<TResponse>(path, "PATCH", body);
}

export function deleteJson<TResponse>(path: string, body?: unknown): Promise<TResponse> {
  return sendJson<TResponse>(path, "DELETE", body);
}

export function getAlertSocketUrl() {
  if (typeof window === "undefined") {
    return "ws://localhost/ws/alerts";
  }

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws/alerts`;
}