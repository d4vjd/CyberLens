// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import type { PropsWithChildren } from "react";

type TooltipProps = PropsWithChildren<{
  content: string;
  block?: boolean;
}>;

export function Tooltip({ content, block = false, children }: TooltipProps) {
  return (
    <span className={block ? "tooltip tooltip--block" : "tooltip"}>
      <span className={block ? "tooltip__trigger tooltip__trigger--block" : "tooltip__trigger"}>
        {children}
      </span>
      <span aria-hidden="true" className="tooltip__content" role="tooltip">
        {content}
      </span>
    </span>
  );
}
