import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api";
import type {
  CanonicalEntity,
  CountryCandidate,
  EntityKind,
  NormalizationCandidate,
} from "../types/normalization";

const chipClass =
  "rounded-md border border-border-default bg-bg-raised px-2 py-1 text-xs text-text-secondary hover:bg-white/10 disabled:opacity-50";

function statusText(kind: string, loading: boolean, empty: boolean) {
  if (loading) return `Finding ${kind} matches...`;
  if (empty) return `No canonical ${kind} match`;
  return null;
}

function EntityCandidateChips({
  candidates,
  selectedId,
  creating,
  createLabel,
  onCreate,
  onSelect,
}: {
  candidates: NormalizationCandidate[];
  selectedId: string | null;
  creating: boolean;
  createLabel: string;
  onCreate: () => void;
  onSelect: (candidate: NormalizationCandidate) => void;
}) {
  return (
    <>
      {candidates.map((candidate) => (
        <button
          key={candidate.id}
          type="button"
          onClick={() => onSelect(candidate)}
          className={chipClass}
        >
          {candidate.canonical_name}
        </button>
      ))}
      {!selectedId && (
        <button type="button" onClick={onCreate} disabled={creating} className={chipClass}>
          {creating ? "Creating..." : createLabel}
        </button>
      )}
    </>
  );
}

function useEntityCandidates(kind: EntityKind, query: string) {
  const [candidates, setCandidates] = useState<NormalizationCandidate[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!query) {
      setCandidates([]);
      return;
    }

    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setLoading(true);
      api
        .get(`/api/normalization/candidates?kind=${kind}&q=${encodeURIComponent(query)}`, {
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
  }, [kind, query]);

  return { candidates, loading, setCandidates };
}

export function EntityCandidatePicker({
  kind,
  value,
  selectedId,
  onSelect,
}: {
  kind: EntityKind;
  value: string;
  selectedId: string | null;
  onSelect: (entity: { id: string; name: string }) => void;
}) {
  const [creating, setCreating] = useState(false);
  const query = value.trim();
  const { candidates, loading, setCandidates } = useEntityCandidates(kind, query);
  const selected = useMemo(
    () => candidates.find((candidate) => candidate.id === selectedId),
    [candidates, selectedId],
  );

  const selectCandidate = useCallback(
    (candidate: NormalizationCandidate) => {
      onSelect({ id: candidate.id, name: candidate.canonical_name });
    },
    [onSelect],
  );

  const createEntity = useCallback(async () => {
    if (!query) return;
    setCreating(true);
    try {
      const res = await api.post("/api/entities", { kind, name: query });
      if (!res.ok) return;
      const entity: CanonicalEntity = await res.json();
      onSelect({ id: entity.id, name: entity.name });
      setCandidates((prev) => [
        {
          id: entity.id,
          kind: entity.kind,
          canonical_name: entity.name,
          aliases: [],
          score: 1,
          match_reason: "created",
        },
        ...prev,
      ]);
    } finally {
      setCreating(false);
    }
  }, [kind, onSelect, query, setCandidates]);

  if (!query) return null;

  const message = statusText(kind, loading, candidates.length === 0);

  return (
    <div className="flex min-h-7 flex-wrap items-center gap-2">
      {message && <span className="text-xs text-text-muted">{message}</span>}
      {!loading && (
        <EntityCandidateChips
          candidates={candidates}
          selectedId={selected?.id ?? selectedId}
          creating={creating}
          createLabel={`Create ${kind}`}
          onCreate={() => void createEntity()}
          onSelect={(candidate) => void selectCandidate(candidate)}
        />
      )}
    </div>
  );
}

export function CountryCandidatePicker({
  value,
  selectedCode,
  onSelect,
}: {
  value: string;
  selectedCode: string | null;
  onSelect: (country: CountryCandidate) => void;
}) {
  const [candidates, setCandidates] = useState<CountryCandidate[]>([]);
  const [loading, setLoading] = useState(false);
  const query = value.trim();

  useEffect(() => {
    if (!query) {
      setCandidates([]);
      return;
    }

    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setLoading(true);
      api
        .get(`/api/normalization/countries?q=${encodeURIComponent(query)}`, {
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
  }, [query]);

  if (!query || selectedCode) return null;

  const message = statusText("country", loading, candidates.length === 0);

  return (
    <div className="flex min-h-7 flex-wrap items-center gap-2">
      {message && <span className="text-xs text-text-muted">{message}</span>}
      {!loading &&
        candidates.map((candidate) => (
          <button
            key={candidate.code}
            type="button"
            onClick={() => onSelect(candidate)}
            className={chipClass}
          >
            {candidate.name}
          </button>
        ))}
    </div>
  );
}
