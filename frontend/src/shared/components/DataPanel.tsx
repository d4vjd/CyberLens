// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import { PropsWithChildren, ReactNode } from "react";

type DataPanelProps = PropsWithChildren<{
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}>;

export function DataPanel({ title, subtitle, actions, children }: DataPanelProps) {
  return (
    <section className="data-panel">
      <div className="data-panel__header">
        <div>
          <h4>{title}</h4>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
        {actions ? <div className="data-panel__actions">{actions}</div> : null}
      </div>
      {children}
    </section>
  );
}