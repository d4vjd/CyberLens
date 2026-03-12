// CyberLens SIEM — Copyright (c) 2026 David Pupăză
// Licensed under the Hippocratic License 3.0. See LICENSE file for details.

import type { ReactNode } from "react";

type Column<T> = {
  header: string;
  render: (item: T) => ReactNode;
};

type DataTableProps<T> = {
  columns: Column<T>[];
  items: T[];
  rowKey: (item: T) => string | number;
  emptyMessage: string;
  onRowClick?: (item: T) => void;
};

export function DataTable<T>({
  columns,
  items,
  rowKey,
  emptyMessage,
  onRowClick,
}: DataTableProps<T>) {
  return (
    <table className="data-table">
      <thead>
        <tr>
          {columns.map((column) => (
            <th key={column.header}>{column.header}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {items.length ? (
          items.map((item) => (
            <tr
              className={onRowClick ? "data-table__row data-table__row--interactive" : "data-table__row"}
              key={rowKey(item)}
              onClick={() => onRowClick?.(item)}
            >
              {columns.map((column) => (
                <td key={column.header}>{column.render(item)}</td>
              ))}
            </tr>
          ))
        ) : (
          <tr>
            <td className="table-message" colSpan={columns.length}>
              {emptyMessage}
            </td>
          </tr>
        )}
      </tbody>
    </table>
  );
}