import { useEffect, useState } from "react";
import { api } from "../api";
import type { NormalizationCandidate } from "../types/normalization";

export function ProcessCandidatePicker({
  value,
  onSelect,
}: {
  value: string;
  onSelect: (value: string) => void;
}) {
  const [candidates, setCandidates] = useState<NormalizationCandidate[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const query = value.trim();
    if (!query) {
      setCandidates([]);
      return;
    }

    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setLoading(true);
      api
        .get(`/api/normalization/candidates?kind=process&q=${encodeURIComponent(query)}`, {
          signal: controller.signal,
        })
        .then((res) => (res.ok ? res.json() : []))
        .then((data) => setCandidates(data))
        .catch(() => {
          if (!controller.signal.aborted) setCandidates([]);
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false);
        });
    }, 250);

    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [value]);

  if (!value.trim()) return null;

  return (
    <div className="flex min-h-7 flex-wrap items-center gap-2">
      {loading && <span className="text-xs text-text-muted">Finding process matches...</span>}
      {!loading &&
        candidates.map((candidate) => (
          <button
            key={candidate.id}
            type="button"
            onClick={() => onSelect(candidate.canonical_name)}
            className="rounded-md border border-border-default bg-bg-raised px-2 py-1 text-xs text-text-secondary hover:bg-white/10"
          >
            {candidate.canonical_name}
          </button>
        ))}
      {!loading && candidates.length === 0 && (
        <span className="text-xs text-text-muted">No canonical process match</span>
      )}
    </div>
  );
}
