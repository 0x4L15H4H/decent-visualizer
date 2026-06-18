import { useCallback, useEffect, useState } from "react";
import { api } from "../api";

interface AppSettings {
  signups_enabled: boolean;
}

function ToggleRow({
  label,
  description,
  checked,
  onChange,
  disabled,
}: {
  label: string;
  description: string;
  checked: boolean;
  onChange: (value: boolean) => void;
  disabled: boolean;
}) {
  return (
    <div className="flex items-center justify-between py-3">
      <div>
        <p className="text-sm font-medium text-text-primary">{label}</p>
        <p className="text-xs text-text-muted">{description}</p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border border-border-default transition-colors disabled:opacity-50 ${checked ? "bg-accent" : "bg-bg-raised"}`}
      >
        <span
          className={`pointer-events-none inline-block h-4 w-4 rounded-full bg-text-primary shadow transition-transform ${checked ? "translate-x-4" : "translate-x-0"}`}
        />
      </button>
    </div>
  );
}

function Settings() {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api
      .get("/api/settings")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => setSettings(data))
      .catch(() => setSettings(null));
  }, []);

  const update = useCallback(async (patch: Partial<AppSettings>) => {
    setSaving(true);
    try {
      const res = await api.patch("/api/settings", patch);
      if (res.ok) setSettings(await res.json());
    } finally {
      setSaving(false);
    }
  }, []);

  if (!settings) {
    return (
      <div className="rounded-lg border border-border-default bg-bg-surface p-4">
        <div className="h-4 w-48 animate-pulse rounded bg-bg-raised" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="mt-1 text-sm text-text-secondary">
          Manage your instance configuration.
        </p>
      </div>
      <div className="rounded-lg border border-border-default bg-bg-surface p-4">
        <h2 className="mb-1 text-sm font-medium text-text-muted">Authentication</h2>
        <div className="divide-y divide-border-subtle">
          <ToggleRow
            label="Allow signups"
            description="When disabled, only existing users can log in."
            checked={settings.signups_enabled}
            onChange={(v) => update({ signups_enabled: v })}
            disabled={saving}
          />
        </div>
      </div>
    </div>
  );
}

export default Settings;
