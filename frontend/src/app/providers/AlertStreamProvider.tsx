// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import { createContext, PropsWithChildren, useContext, useEffect, useState } from "react";

import { useDemoStore } from "../store/demoStore";
import { useWebSocket } from "../../shared/hooks/useWebSocket";
import { getAlertSocketUrl } from "../../shared/utils/api";
import { getSyntheticAlerts } from "../../shared/utils/mockData";
import type { AlertRecord, ConnectionState } from "../../shared/types";

type AlertStreamContextValue = {
  connectionState: ConnectionState;
  recentAlerts: AlertRecord[];
  unseenCount: number;
  clearUnseen: () => void;
};

const AlertStreamContext = createContext<AlertStreamContextValue | null>(null);

function isAlertMessage(payload: unknown): payload is { type: string; payload: AlertRecord } {
  if (!payload || typeof payload !== "object") {
    return false;
  }

  const typedPayload = payload as { type?: unknown; payload?: unknown };
  return typedPayload.type === "alert" && !!typedPayload.payload;
}

export function AlertStreamProvider({ children }: PropsWithChildren) {
  const dataSource = useDemoStore((state) => state.dataSource);
  const liveStream = useDemoStore((state) => state.liveStream);
  const [recentAlerts, setRecentAlerts] = useState<AlertRecord[]>([]);
  const [unseenCount, setUnseenCount] = useState(0);
  const liveConnectionState = useWebSocket({
    enabled: dataSource === "live" && liveStream,
    url: getAlertSocketUrl(),
    onMessage: (message) => {
      if (!isAlertMessage(message)) {
        return;
      }

      setRecentAlerts((current) => [message.payload, ...current].slice(0, 6));
      setUnseenCount((current) => current + 1);
    },
  });

  useEffect(() => {
    if (dataSource === "synthetic") {
      setRecentAlerts(getSyntheticAlerts().items.slice(0, 4));
      setUnseenCount(0);
      return;
    }

    setRecentAlerts([]);
    setUnseenCount(0);
  }, [dataSource]);

  const connectionState: ConnectionState =
    dataSource === "synthetic" ? "synthetic" : liveConnectionState;

  return (
    <AlertStreamContext.Provider
      value={{
        connectionState,
        recentAlerts,
        unseenCount,
        clearUnseen: () => setUnseenCount(0),
      }}
    >
      {children}
    </AlertStreamContext.Provider>
  );
}

export function useAlertStream() {
  const context = useContext(AlertStreamContext);
  if (!context) {
    throw new Error("useAlertStream must be used within AlertStreamProvider");
  }
  return context;
}