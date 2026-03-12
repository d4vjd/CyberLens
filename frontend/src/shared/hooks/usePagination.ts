// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import { useCallback, useEffect, useState } from "react";

export function usePagination(pageSize = 10) {
  const [page, setPage] = useState(0);
  const reset = useCallback(() => setPage(0), []);

  useEffect(() => {
    setPage(0);
  }, [pageSize]);

  return {
    page,
    pageSize,
    setPage,
    reset,
  };
}