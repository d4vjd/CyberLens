// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import { PropsWithChildren, ReactNode } from "react";

type PageIntroProps = PropsWithChildren<{
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
}>;

export function PageIntro({
  eyebrow,
  title,
  description,
  actions,
  children,
}: PageIntroProps) {
  return (
    <section className="page-section">
      <div className="page-intro">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h3>{title}</h3>
          <p className="page-intro__description">{description}</p>
        </div>
        {actions ? <div className="page-intro__actions">{actions}</div> : null}
      </div>
      {children}
    </section>
  );
}