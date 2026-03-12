// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import { useEffect, useRef, useState } from "react";

import type { ConnectionState } from "../types";

type UseWebSocketOptions = {
  enabled: boolean;
  url: string;
  onMessage: (payload: unknown) => void;
};

export function useWebSocket({ enabled, url, onMessage }: UseWebSocketOptions) {
  const onMessageRef = useRef(onMessage);
  const retryTimeoutRef = useRef<number | null>(null);
  const attemptRef = useRef(0);
  const [connectionState, setConnectionState] = useState<ConnectionState>(
    enabled ? "connecting" : "offline",
  );

  onMessageRef.current = onMessage;

  useEffect(() => {
    if (!enabled) {
      setConnectionState("offline");
      return undefined;
    }

    let socket: WebSocket | null = null;
    let closedByEffect = false;

    function cleanupRetry() {
      if (retryTimeoutRef.current !== null) {
        window.clearTimeout(retryTimeoutRef.current);
        retryTimeoutRef.current = null;
      }
    }

    function connect() {
      cleanupRetry();
      setConnectionState(attemptRef.current === 0 ? "connecting" : "reconnecting");
      socket = new WebSocket(url);

      socket.onopen = () => {
        attemptRef.current = 0;
        setConnectionState("connected");
      };

      socket.onmessage = (event) => {
        try {
          onMessageRef.current(JSON.parse(event.data));
        } catch {
          onMessageRef.current(event.data);
        }
      };

      socket.onerror = () => {
        socket?.close();
      };

      socket.onclose = () => {
        if (closedByEffect) {
          return;
        }

        attemptRef.current += 1;
        const delay = Math.min(30_000, 1_000 * 2 ** (attemptRef.current - 1));
        const jitter = Math.round(Math.random() * 350);
        setConnectionState("reconnecting");
        retryTimeoutRef.current = window.setTimeout(connect, delay + jitter);
      };
    }

    connect();

    return () => {
      closedByEffect = true;
      cleanupRetry();
      socket?.close();
    };
  }, [enabled, url]);

  return connectionState;
}