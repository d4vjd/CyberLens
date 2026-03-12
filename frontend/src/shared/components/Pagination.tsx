// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

type PaginationProps = {
  currentPage: number;
  totalPages: number;
  onPrevious: () => void;
  onNext: () => void;
};

export function Pagination({
  currentPage,
  totalPages,
  onPrevious,
  onNext,
}: PaginationProps) {
  return (
    <div className="pagination">
      <button className="ghost-button" disabled={currentPage <= 1} onClick={onPrevious} type="button">
        Previous
      </button>
      <span>
        Page {currentPage} / {Math.max(totalPages, 1)}
      </span>
      <button
        className="ghost-button"
        disabled={currentPage >= totalPages}
        onClick={onNext}
        type="button"
      >
        Next
      </button>
    </div>
  );
}