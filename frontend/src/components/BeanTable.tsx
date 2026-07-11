import { useMemo } from "react";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
  type OnChangeFn,
  type SortingState,
} from "@tanstack/react-table";
import type { Bean } from "../types/bean";

export const BEAN_PAGE_SIZE = 20;
const col = createColumnHelper<Bean>();

const paginationBtnClass =
  "rounded-md border border-border-default bg-bg-raised px-2 py-1 text-xs text-text-secondary hover:bg-white/10 disabled:opacity-30 disabled:pointer-events-none";

function BeanSearch({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return (
    <label className="relative block">
      <span className="sr-only">Search beans</span>
      <input
        type="search"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Search beans"
        className="h-9 w-full rounded-md border border-border-default bg-bg-raised px-3 text-sm text-text-primary outline-none placeholder:text-text-muted focus:ring-1 focus:ring-accent"
      />
    </label>
  );
}

function BeanPagination({
  pageIndex,
  pageCount,
  canGoBack,
  canGoForward,
  onPrevious,
  onNext,
}: {
  pageIndex: number;
  pageCount: number;
  canGoBack: boolean;
  canGoForward: boolean;
  onPrevious: () => void;
  onNext: () => void;
}) {
  if (pageCount <= 1) return null;
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-text-muted">
        Page {pageIndex + 1} of {pageCount}
      </span>
      <div className="flex gap-2">
        <button
          type="button"
          disabled={!canGoBack}
          onClick={onPrevious}
          className={paginationBtnClass}
        >
          Previous
        </button>
        <button
          type="button"
          disabled={!canGoForward}
          onClick={onNext}
          className={paginationBtnClass}
        >
          Next
        </button>
      </div>
    </div>
  );
}

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
    col.accessor((bean) => bean.roaster.name, {
      id: "roaster",
      header: "Roaster",
      cell: (info) => info.getValue(),
    }),
    col.accessor((bean) => bean.country?.name ?? "", {
      id: "country",
      header: "Country",
      cell: (info) => info.getValue(),
    }),
    col.accessor((bean) => bean.variety?.name ?? "", {
      id: "variety",
      header: "Variety",
      cell: (info) => info.getValue(),
    }),
    col.accessor((bean) => bean.process?.name ?? "", {
      id: "process",
      header: "Process",
      cell: (info) => info.getValue(),
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

export function BeanTable({
  data,
  total,
  pageIndex,
  query,
  sorting,
  onQueryChange,
  onPageChange,
  onSortingChange,
  onEdit,
}: {
  data: Bean[];
  total: number;
  pageIndex: number;
  query: string;
  sorting: SortingState;
  onQueryChange: (value: string) => void;
  onPageChange: (page: number) => void;
  onSortingChange: OnChangeFn<SortingState>;
  onEdit: (bean: Bean) => void;
}) {
  const columns = useMemo(() => createBeanColumns(onEdit), [onEdit]);
  const pageCount = Math.ceil(total / BEAN_PAGE_SIZE);

  const table = useReactTable({
    data,
    columns,
    state: { sorting, pagination: { pageIndex, pageSize: BEAN_PAGE_SIZE } },
    pageCount,
    manualPagination: true,
    manualSorting: true,
    onSortingChange,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div className="flex flex-col gap-3">
      <BeanSearch value={query} onChange={onQueryChange} />
      <div className="overflow-x-auto rounded-lg border border-border-default bg-bg-surface">
        <table className="w-full text-sm">
          <thead>
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id} className="border-b border-border-default">
                {hg.headers.map((header) => (
                  <th
                    key={header.id}
                    onClick={header.column.getToggleSortingHandler()}
                    className={`px-4 py-2 text-left text-xs font-medium text-text-muted select-none ${
                      header.column.getCanSort() ? "cursor-pointer hover:text-text-secondary" : ""
                    }`}
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    {{ asc: " ↑", desc: " ↓" }[header.column.getIsSorted() as string] ?? ""}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-6 text-center text-sm text-text-muted"
                >
                  No beans match your search.
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  className="border-b border-border-subtle last:border-b-0 hover:bg-bg-raised"
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-2 text-text-secondary">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <BeanPagination
        pageIndex={pageIndex}
        pageCount={pageCount}
        canGoBack={pageIndex > 0}
        canGoForward={pageIndex + 1 < pageCount}
        onPrevious={() => onPageChange(pageIndex - 1)}
        onNext={() => onPageChange(pageIndex + 1)}
      />
    </div>
  );
}
