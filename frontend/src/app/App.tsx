// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import { BrowserRouter } from "react-router-dom";

import { AppProviders } from "./providers/AppProviders";
import { AppRoutes } from "./routes";

export function App() {
  return (
    <AppProviders>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AppProviders>
  );
}