import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
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
import { api } from "../api";
import { PhotoExtractButton, type ExtractedBean } from "../components/PhotoExtractButton";

interface Bean {
  id: string;
  name: string;
  roaster: string;
  producer: string | null;
  farm: string | null;
  country: string | null;
  variety: string | null;
  process: string | null;
  notes: string | null;
  created_at: string;
}

const inputClass =
  "w-full rounded-md border border-border-default bg-bg-raised px-3 py-1.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-accent";

function AddBeanForm({ onCreated }: { onCreated: (bean: Bean) => void }) {
  const [name, setName] = useState("");
  const [roaster, setRoaster] = useState("");
  const [producer, setProducer] = useState("");
  const [farm, setFarm] = useState("");
  const [country, setCountry] = useState("");
  const [variety, setVariety] = useState("");
  const [process, setProcess] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleExtracted = useCallback((data: ExtractedBean) => {
    if (data.name) setName(data.name);
    if (data.roaster) setRoaster(data.roaster);
    if (data.producer) setProducer(data.producer);
    if (data.farm) setFarm(data.farm);
    if (data.country) setCountry(data.country);
    if (data.variety) setVariety(data.variety);
    if (data.process) setProcess(data.process);
    if (data.notes) setNotes(data.notes);
  }, []);

  const handleSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();
      setError(null);
      setSubmitting(true);
      try {
        const res = await api.post("/api/beans", {
          name,
          roaster,
          producer: producer || null,
          farm: farm || null,
          country: country || null,
          variety: variety || null,
          process: process || null,
          notes: notes || null,
        });
        if (!res.ok) {
          const body = await res.json();
          throw new Error(body.detail ?? "Failed to create bean");
        }
        onCreated(await res.json());
      } catch (err) {
        setError(err instanceof Error ? err.message : "Something went wrong");
      } finally {
        setSubmitting(false);
      }
    },
    [name, roaster, producer, farm, country, variety, process, notes, onCreated],
  );

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <PhotoExtractButton onExtracted={handleExtracted} />
      <div className="grid grid-cols-2 gap-3">
        <input type="text" placeholder="Name *" required value={name} onChange={(e) => setName(e.target.value)} className={inputClass} />
        <input type="text" placeholder="Roaster *" required value={roaster} onChange={(e) => setRoaster(e.target.value)} className={inputClass} />
        <input type="text" placeholder="Producer" value={producer} onChange={(e) => setProducer(e.target.value)} className={inputClass} />
        <input type="text" placeholder="Farm" value={farm} onChange={(e) => setFarm(e.target.value)} className={inputClass} />
        <input type="text" placeholder="Country" value={country} onChange={(e) => setCountry(e.target.value)} className={inputClass} />
        <input type="text" placeholder="Variety" value={variety} onChange={(e) => setVariety(e.target.value)} className={inputClass} />
        <input type="text" placeholder="Process" value={process} onChange={(e) => setProcess(e.target.value)} className={inputClass} />
      </div>
      <textarea
        placeholder="Flavor notes"
        rows={2}
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        className={inputClass + " resize-none"}
      />
      {error && <p className="text-sm text-destructive">{error}</p>}
      <div className="flex justify-end">
        <button
          type="submit"
          disabled={submitting}
          className="rounded-md border border-border-default bg-bg-raised px-3 py-1.5 text-sm font-medium text-text-primary hover:bg-white/10 disabled:opacity-50"
        >
          {submitting ? "..." : "Add bean"}
        </button>
      </div>
    </form>
  );
}

const col = createColumnHelper<Bean>();

const columns = [
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
];

const PAGE_SIZE = 20;

const paginationBtnClass =
  "rounded-md border border-border-default bg-bg-raised px-2 py-1 text-xs text-text-secondary hover:bg-white/10 disabled:opacity-30 disabled:pointer-events-none";

function BeanTable({ data }: { data: Bean[] }) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: PAGE_SIZE,
  });

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

function Beans() {
  const [beans, setBeans] = useState<Bean[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    api
      .get("/api/beans")
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => setBeans(data))
      .catch(() => setBeans([]))
      .finally(() => setLoading(false));
  }, []);

  const handleCreated = useCallback((bean: Bean) => {
    setBeans((prev) => [bean, ...prev]);
    setShowForm(false);
  }, []);

  const stableData = useMemo(() => beans, [beans]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Beans</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Your coffee bean library.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowForm(!showForm)}
          className="rounded-md border border-border-default bg-bg-raised px-3 py-1.5 text-sm font-medium text-text-primary hover:bg-white/10"
        >
          {showForm ? "Cancel" : "Add bean"}
        </button>
      </div>

      {showForm && (
        <div className="rounded-lg border border-border-default bg-bg-surface p-4">
          <AddBeanForm onCreated={handleCreated} />
        </div>
      )}

      {loading ? (
        <div className="rounded-lg border border-border-default bg-bg-surface p-4">
          <div className="h-4 w-48 animate-pulse rounded bg-bg-raised" />
        </div>
      ) : beans.length === 0 ? (
        <div className="rounded-lg border border-border-default bg-bg-surface p-4">
          <p className="text-sm text-text-secondary">
            No beans yet. Add a coffee to start tracking your brews.
          </p>
        </div>
      ) : (
        <BeanTable data={stableData} />
      )}
    </div>
  );
}

export default Beans;
