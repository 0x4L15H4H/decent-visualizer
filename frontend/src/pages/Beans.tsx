import { useCallback, useEffect, useState, type Dispatch, type SetStateAction } from "react";
import type { SortingState } from "@tanstack/react-table";
import { api } from "../api";
import { BeanForm } from "../components/BeanForm";
import { BEAN_PAGE_SIZE, BeanTable } from "../components/BeanTable";
import {
  beanPayload,
  emptyBeanFormValues,
  valuesFromBean,
  type Bean,
  type BeanFormValues,
} from "../types/bean";

const buttonClass =
  "rounded-md border border-border-default bg-bg-raised px-3 py-1.5 text-sm font-medium text-text-primary hover:bg-white/10 disabled:opacity-50";

interface BeanPage {
  items: Bean[];
  total: number;
  page: number;
  page_size: number;
}

function AddBeanPanel({ onSubmit }: { onSubmit: (values: BeanFormValues) => Promise<void> }) {
  return (
    <div className="rounded-lg border border-border-default bg-bg-surface p-4">
      <BeanForm
        initialValues={emptyBeanFormValues}
        submitLabel="Add bean"
        busyLabel="Adding..."
        onSubmit={onSubmit}
      />
    </div>
  );
}

function EditBeanPanel({
  bean,
  onSubmit,
  onCancel,
}: {
  bean: Bean;
  onSubmit: (values: BeanFormValues) => Promise<void>;
  onCancel: () => void;
}) {
  return (
    <div className="rounded-lg border border-border-default bg-bg-surface p-4">
      <div className="mb-3">
        <h2 className="text-sm font-medium text-text-primary">Edit bean</h2>
        <p className="mt-1 text-xs text-text-muted">
          Update bean details before normalization rules are introduced.
        </p>
      </div>
      <BeanForm
        initialValues={valuesFromBean(bean)}
        submitLabel="Save changes"
        busyLabel="Saving..."
        onSubmit={onSubmit}
        onCancel={onCancel}
      />
    </div>
  );
}

function BeanListState({
  loading,
  beans,
  total,
  pageIndex,
  query,
  sorting,
  onQueryChange,
  onPageChange,
  onSortingChange,
  onEdit,
}: {
  loading: boolean;
  beans: Bean[];
  total: number;
  pageIndex: number;
  query: string;
  sorting: SortingState;
  onQueryChange: (value: string) => void;
  onPageChange: (page: number) => void;
  onSortingChange: Dispatch<SetStateAction<SortingState>>;
  onEdit: (bean: Bean) => void;
}) {
  if (loading && beans.length === 0 && !query) {
    return (
      <div className="rounded-lg border border-border-default bg-bg-surface p-4">
        <div className="h-4 w-48 animate-pulse rounded bg-bg-raised" />
      </div>
    );
  }

  if (total === 0 && !query) {
    return (
      <div className="rounded-lg border border-border-default bg-bg-surface p-4">
        <p className="text-sm text-text-secondary">
          No beans yet. Add a coffee to start tracking your brews.
        </p>
      </div>
    );
  }

  return (
    <BeanTable
      data={beans}
      total={total}
      pageIndex={pageIndex}
      query={query}
      sorting={sorting}
      onQueryChange={onQueryChange}
      onPageChange={onPageChange}
      onSortingChange={onSortingChange}
      onEdit={onEdit}
    />
  );
}

function useBeanPage() {
  const [beans, setBeans] = useState<Bean[]>([]);
  const [total, setTotal] = useState(0);
  const [pageIndex, setPageIndex] = useState(0);
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [sorting, setSorting] = useState<SortingState>([]);
  const [refreshKey, setRefreshKey] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timeout = window.setTimeout(() => setDebouncedQuery(query.trim()), 250);
    return () => window.clearTimeout(timeout);
  }, [query]);

  useEffect(() => {
    const controller = new AbortController();
    const params = new URLSearchParams({
      page: String(pageIndex + 1),
      page_size: String(BEAN_PAGE_SIZE),
    });
    if (debouncedQuery) params.set("q", debouncedQuery);
    const sort = sorting[0];
    if (sort) {
      params.set("sort_by", sort.id);
      params.set("sort_dir", sort.desc ? "desc" : "asc");
    }
    setLoading(true);
    api
      .get(`/api/beans?${params.toString()}`, { signal: controller.signal })
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load beans");
        return res.json() as Promise<BeanPage>;
      })
      .then((data) => {
        setBeans(data.items);
        setTotal(data.total);
      })
      .catch(() => {
        if (controller.signal.aborted) return;
        setBeans([]);
        setTotal(0);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [debouncedQuery, pageIndex, refreshKey, sorting]);

  const refresh = useCallback(() => setRefreshKey((current) => current + 1), []);

  return {
    beans,
    total,
    pageIndex,
    query,
    sorting,
    loading,
    setPageIndex,
    setQuery,
    setSorting,
    refresh,
  };
}

function Beans() {
  const {
    beans,
    total,
    pageIndex,
    query,
    sorting,
    loading,
    setPageIndex,
    setQuery,
    setSorting,
    refresh,
  } = useBeanPage();
  const [showForm, setShowForm] = useState(false);
  const [editingBean, setEditingBean] = useState<Bean | null>(null);

  const handleCreate = useCallback(
    async (values: BeanFormValues) => {
      const res = await api.post("/api/beans", beanPayload(values));
      if (!res.ok) {
        const body = await res.json();
        throw new Error(body.detail ?? "Failed to create bean");
      }
      setPageIndex(0);
      refresh();
      setShowForm(false);
    },
    [refresh, setPageIndex],
  );

  const handleEdit = useCallback((bean: Bean) => {
    setEditingBean(bean);
    setShowForm(false);
  }, []);

  const handleUpdate = useCallback(
    async (values: BeanFormValues) => {
      if (!editingBean) return;
      const res = await api.patch(`/api/beans/${editingBean.id}`, beanPayload(values));
      if (!res.ok) {
        const body = await res.json();
        throw new Error(body.detail ?? "Failed to update bean");
      }
      refresh();
      setEditingBean(null);
    },
    [editingBean, refresh],
  );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Beans</h1>
          <p className="mt-1 text-sm text-text-secondary">Your coffee bean library.</p>
        </div>
        <button
          type="button"
          onClick={() => {
            setShowForm(!showForm);
            setEditingBean(null);
          }}
          className={buttonClass}
        >
          {showForm ? "Cancel" : "Add bean"}
        </button>
      </div>

      {showForm && <AddBeanPanel onSubmit={handleCreate} />}
      {editingBean && (
        <EditBeanPanel
          bean={editingBean}
          onSubmit={handleUpdate}
          onCancel={() => setEditingBean(null)}
        />
      )}
      <BeanListState
        loading={loading}
        beans={beans}
        total={total}
        pageIndex={pageIndex}
        query={query}
        sorting={sorting}
        onQueryChange={(value) => {
          setQuery(value);
          setPageIndex(0);
        }}
        onPageChange={setPageIndex}
        onSortingChange={(updater) => {
          setSorting(updater);
          setPageIndex(0);
        }}
        onEdit={handleEdit}
      />
    </div>
  );
}

export default Beans;
