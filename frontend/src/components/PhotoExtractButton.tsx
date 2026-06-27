import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api";

export interface ExtractedBean {
  name?: string | null;
  roaster?: CanonicalSelection | null;
  producer?: CanonicalSelection | null;
  farm?: CanonicalSelection | null;
  country?: CanonicalSelection | null;
  variety?: CanonicalSelection | null;
  process?: CanonicalSelection | null;
  notes?: string | null;
}

interface CanonicalSelection {
  resolution: "matched" | "proposed";
  canonical_id: string | null;
  name: string;
}

export function PhotoExtractButton({
  onExtracted,
}: {
  onExtracted: (data: ExtractedBean) => void;
}) {
  const [enabled, setEnabled] = useState<boolean | null>(null);
  const [extracting, setExtracting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api
      .get("/api/beans/photo-extract/enabled")
      .then((res) => (res.ok ? res.json() : { enabled: false }))
      .then((data) => setEnabled(data.enabled))
      .catch(() => setEnabled(false));
  }, []);

  const handleFile = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;
      setError(null);
      setExtracting(true);
      try {
        const res = await api.upload("/api/beans/photo-extract/upload", file);
        if (!res.ok) {
          const body = await res.json();
          throw new Error(body.detail ?? "Failed to extract");
        }
        onExtracted(await res.json());
      } catch (err) {
        setError(err instanceof Error ? err.message : "Extraction failed");
      } finally {
        setExtracting(false);
        if (fileRef.current) fileRef.current.value = "";
      }
    },
    [onExtracted],
  );

  if (enabled === null) return null;

  const disabled = !enabled || extracting;
  const label = extracting ? "Extracting..." : "Scan from photo";

  return (
    <div className="flex items-center gap-3">
      <input ref={fileRef} type="file" accept="image/*" onChange={handleFile} className="hidden" />
      <button
        type="button"
        disabled={disabled}
        onClick={() => fileRef.current?.click()}
        className="rounded-md border border-dashed border-border-default bg-bg-raised px-3 py-1.5 text-sm text-text-secondary hover:bg-white/10 disabled:opacity-50"
      >
        {label}
      </button>
      {!enabled && <span className="text-xs text-text-muted">Photo extraction not configured</span>}
      {error && <span className="text-xs text-destructive">{error}</span>}
    </div>
  );
}
