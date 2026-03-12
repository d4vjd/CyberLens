// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import { Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "./layout/AppLayout";
import { AlertsPage } from "../features/alerts/AlertsPage";
import { AnalyticsPage } from "../features/analytics/AnalyticsPage";
import { CasesPage } from "../features/cases/CasesPage";
import { EventsPage } from "../features/events/EventsPage";
import { MitrePage } from "../features/mitre/MitrePage";
import { OverviewPage } from "../features/overview/OverviewPage";
import { RulesPage } from "../features/rules/RulesPage";
import { SettingsPage } from "../features/settings/SettingsPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppLayout />} path="/">
        <Route element={<OverviewPage />} index />
        <Route element={<EventsPage />} path="events" />
        <Route element={<AlertsPage />} path="alerts" />
        <Route element={<MitrePage />} path="mitre" />
        <Route element={<CasesPage />} path="cases" />
        <Route element={<RulesPage />} path="rules" />
        <Route element={<AnalyticsPage />} path="analytics" />
        <Route element={<SettingsPage />} path="settings" />
        <Route element={<Navigate replace to="/" />} path="*" />
      </Route>
    </Routes>
  );
}