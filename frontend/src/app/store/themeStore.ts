// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import { create } from "zustand";

type ThemeMode = "night" | "dawn";

type ThemeState = {
  theme: ThemeMode;
  toggleTheme: () => void;
};

const storageKey = "cyberlens-theme";

function readTheme(): ThemeMode {
  if (typeof window === "undefined") {
    return "night";
  }

  return window.localStorage.getItem(storageKey) === "dawn" ? "dawn" : "night";
}

export const useThemeStore = create<ThemeState>((set) => ({
  theme: readTheme(),
  toggleTheme: () =>
    set((state) => {
      const theme = state.theme === "night" ? "dawn" : "night";
      if (typeof window !== "undefined") {
        window.localStorage.setItem(storageKey, theme);
      }
      return { theme };
    }),
}));