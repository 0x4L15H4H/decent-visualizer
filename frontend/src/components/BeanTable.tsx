import { useMemo, useState } from "react";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  type PaginationState,
  type SortingState,
} from "@tanstack/react-table";
import type { Bean } from "../types/bean";

const PAGE_SIZE = 20;
const col = createColumnHelper<Bean>();

const paginationBtnClass =
  "rounded-md border border-border-default bg-bg-raised px-2 py-1 text-xs text-text-secondary hover:bg-white/10 disabled:opacity-30 disabled:pointer-events-none";

function BeanActionsCell({ bean, onEdit }: { bean: Bean; onEdit: (bean: Bean) => void }) {
  return (
    <button type="button" onClick={() => onEdit(bean)} className={paginationBtnClass}>
      Edit
    </button>
  );
}

function createBeanColumns(onEdit: (bean: Bean) => void) {
  return [
    col.accessor("name", {
      header: "Name",
      cell: (info) => info.getValue(),
    }),
    col.accessor("roaster", {
      header: "Roaster",
      cell: (info) => info.getValue(),
    }),
    col.accessor("country", {
      header: "Country",
      cell: (info) => info.getValue() ?? "",
    }),
    col.accessor("variety", {
      header: "Variety",
      cell: (info) => info.getValue() ?? "",
    }),
    col.accessor("process", {
      header: "Process",
      cell: (info) => info.getValue() ?? "",
    }),
    col.accessor("notes", {
      header: "Notes",
      cell: (info) => {
        const v = info.getValue();
        if (!v) return "";
        return v.length > 40 ? v.slice(0, 40) + "..." : v;
      },
    }),
    col.display({
      id: "actions",
      header: "",
      cell: (info) => <BeanActionsCell bean={info.row.original} onEdit={onEdit} />,
    }),
  ];
}

export function BeanTable({ data, onEdit }: { data: Bean[]; onEdit: (bean: Bean) => void }) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: PAGE_SIZE,
  });
  const columns = useMemo(() => createBeanColumns(onEdit), [onEdit]);

  const table = useReactTable({
    data,
    columns,
    state: { sorting, pagination },
    onSortingChange: setSorting,
    onPaginationChange: setPagination,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  const pageCount = table.getPageCount();

  return (
    <div className="flex flex-col gap-3">
      <div className="overflow-x-auto rounded-lg border border-border-default bg-bg-surface">
        <table className="w-full text-sm">
          <thead>
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id} className="border-b border-border-default">
                {hg.headers.map((header) => (
                  <th
                    key={header.id}
                    onClick={header.column.getToggleSortingHandler()}
                    className="cursor-pointer px-4 py-2 text-left text-xs font-medium text-text-muted select-none hover:text-text-secondary"
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    {{ asc: " ↑", desc: " ↓" }[header.column.getIsSorted() as string] ?? ""}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id} className="border-b border-border-subtle last:border-b-0 hover:bg-bg-raised">
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-4 py-2 text-text-secondary">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {pageCount > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-xs text-text-muted">
            Page {pagination.pageIndex + 1} of {pageCount}
          </span>
          <div className="flex gap-2">
            <button type="button" disabled={!table.getCanPreviousPage()} onClick={() => table.previousPage()} className={paginationBtnClass}>
              Previous
            </button>
            <button type="button" disabled={!table.getCanNextPage()} onClick={() => table.nextPage()} className={paginationBtnClass}>
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
