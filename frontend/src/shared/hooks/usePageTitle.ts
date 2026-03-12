// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import { useEffect } from "react";

export function usePageTitle(title: string) {
  useEffect(() => {
    document.title = `${title} | CyberLens`;
  }, [title]);
}