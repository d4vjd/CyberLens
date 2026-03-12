// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import { create } from "zustand";

import type { DataSourceMode } from "../../shared/types";

const storageKey = "cyberlens-demo-preferences";

type DemoState = {
  dataSource: DataSourceMode;
  intensity: number;
  liveStream: boolean;
  preferSyntheticForScreenshots: boolean;
  setDataSource: (dataSource: DataSourceMode) => void;
  setIntensity: (intensity: number) => void;
  setLiveStream: (liveStream: boolean) => void;
  setPreferSyntheticForScreenshots: (prefer: boolean) => void;
};

type StoredPreferences = Pick<
  DemoState,
  "dataSource" | "intensity" | "liveStream" | "preferSyntheticForScreenshots"
>;

function readPreferences(): StoredPreferences {
  if (typeof window === "undefined") {
    return {
      dataSource: "live",
      intensity: 6,
      liveStream: true,
      preferSyntheticForScreenshots: true,
    };
  }

  try {
    const raw = window.localStorage.getItem(storageKey);
    if (!raw) {
      return {
        dataSource: "live",
        intensity: 6,
        liveStream: true,
        preferSyntheticForScreenshots: true,
      };
    }

    const parsed = JSON.parse(raw) as Partial<StoredPreferences>;
    return {
      dataSource: parsed.dataSource === "synthetic" ? "synthetic" : "live",
      intensity:
        typeof parsed.intensity === "number" && parsed.intensity >= 1 && parsed.intensity <= 10
          ? parsed.intensity
          : 6,
      liveStream: parsed.liveStream ?? true,
      preferSyntheticForScreenshots: parsed.preferSyntheticForScreenshots ?? true,
    };
  } catch {
    return {
      dataSource: "live",
      intensity: 6,
      liveStream: true,
      preferSyntheticForScreenshots: true,
    };
  }
}

function persistPreferences(state: DemoState) {
  if (typeof window === "undefined") {
    return;
  }

  const payload: StoredPreferences = {
    dataSource: state.dataSource,
    intensity: state.intensity,
    liveStream: state.liveStream,
    preferSyntheticForScreenshots: state.preferSyntheticForScreenshots,
  };
  window.localStorage.setItem(storageKey, JSON.stringify(payload));
}

const initialState = readPreferences();

export const useDemoStore = create<DemoState>((set, get) => ({
  ...initialState,
  setDataSource: (dataSource) => {
    set({ dataSource });
    persistPreferences(get());
  },
  setIntensity: (intensity) => {
    set({ intensity: Math.min(10, Math.max(1, intensity)) });
    persistPreferences(get());
  },
  setLiveStream: (liveStream) => {
    set({ liveStream });
    persistPreferences(get());
  },
  setPreferSyntheticForScreenshots: (preferSyntheticForScreenshots) => {
    set({ preferSyntheticForScreenshots });
    persistPreferences(get());
  },
}));