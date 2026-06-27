import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { BeanForm } from "../components/BeanForm";
import { BeanTable } from "../components/BeanTable";
import {
  beanPayload,
  emptyBeanFormValues,
  valuesFromBean,
  type Bean,
  type BeanFormValues,
} from "../types/bean";

const buttonClass =
  "rounded-md border border-border-default bg-bg-raised px-3 py-1.5 text-sm font-medium text-text-primary hover:bg-white/10 disabled:opacity-50";

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
  data,
  onEdit,
}: {
  loading: boolean;
  beans: Bean[];
  data: Bean[];
  onEdit: (bean: Bean) => void;
}) {
  if (loading) {
    return (
      <div className="rounded-lg border border-border-default bg-bg-surface p-4">
        <div className="h-4 w-48 animate-pulse rounded bg-bg-raised" />
      </div>
    );
  }

  if (beans.length === 0) {
    return (
      <div className="rounded-lg border border-border-default bg-bg-surface p-4">
        <p className="text-sm text-text-secondary">
          No beans yet. Add a coffee to start tracking your brews.
        </p>
      </div>
    );
  }

  return <BeanTable data={data} onEdit={onEdit} />;
}

function Beans() {
  const [beans, setBeans] = useState<Bean[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingBean, setEditingBean] = useState<Bean | null>(null);

  useEffect(() => {
    api
      .get("/api/beans")
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => setBeans(data))
      .catch(() => setBeans([]))
      .finally(() => setLoading(false));
  }, []);

  const handleCreate = useCallback(async (values: BeanFormValues) => {
    const res = await api.post("/api/beans", beanPayload(values));
    if (!res.ok) {
      const body = await res.json();
      throw new Error(body.detail ?? "Failed to create bean");
    }
    const bean = await res.json();
    setBeans((prev) => [bean, ...prev]);
    setShowForm(false);
  }, []);

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
      const bean = await res.json();
      setBeans((prev) => prev.map((item) => (item.id === bean.id ? bean : item)));
      setEditingBean(null);
    },
    [editingBean],
  );

  const stableData = useMemo(() => beans, [beans]);

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
      <BeanListState loading={loading} beans={beans} data={stableData} onEdit={handleEdit} />
    </div>
  );
}

export default Beans;
