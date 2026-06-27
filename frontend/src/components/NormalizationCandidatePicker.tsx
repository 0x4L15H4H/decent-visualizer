import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { CanonicalTypeahead, type TypeaheadOption } from "./CanonicalTypeahead";
import type {
  CanonicalEntity,
  CountryCandidate,
  EntityKind,
  NormalizationCandidate,
} from "../types/normalization";

function useCandidates<T>(query: string, path: string) {
  const [candidates, setCandidates] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!query.trim()) {
      setCandidates([]);
      setLoading(false);
      setFailed(false);
      return;
    }

    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setLoading(true);
      setFailed(false);
      api
        .get(`${path}${encodeURIComponent(query.trim())}`, { signal: controller.signal })
        .then(async (response) => {
          if (!response.ok) throw new Error("Candidate search failed");
          setCandidates(await response.json());
        })
        .catch(() => {
          if (!controller.signal.aborted) {
            setCandidates([]);
            setFailed(true);
          }
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false);
        });
    }, 250);

    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [path, query]);

  return { candidates, loading, failed, setCandidates };
}

export function EntityCandidatePicker({
  kind,
  value,
  selectedId,
  required,
  onInputChange,
  onSelect,
}: {
  kind: EntityKind;
  value: string;
  selectedId: string | null;
  required?: boolean;
  onInputChange: (value: string) => void;
  onSelect: (entity: TypeaheadOption) => void;
}) {
  const path = `/api/normalization/candidates?kind=${kind}&q=`;
  const { candidates, loading, failed, setCandidates } = useCandidates<NormalizationCandidate>(
    value,
    path,
  );
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const options = useMemo(
    () =>
      candidates.map((candidate) => ({
        id: candidate.id,
        name: candidate.canonical_name,
      })),
    [candidates],
  );

  const createEntity = useCallback(async () => {
    const name = value.trim();
    if (!name) return;
    setCreating(true);
    setCreateError(null);
    try {
      const response = await api.post("/api/entities", { kind, name });
      if (!response.ok) {
        const body = await response.json();
        throw new Error(body.detail ?? `Could not create ${kind}`);
      }
      const entity: CanonicalEntity = await response.json();
      setCandidates((current) => [
        {
          id: entity.id,
          kind: entity.kind,
          canonical_name: entity.name,
          aliases: [],
          score: 1,
          match_reason: "created",
        },
        ...current,
      ]);
      onSelect({ id: entity.id, name: entity.name });
    } catch (error) {
      setCreateError(error instanceof Error ? error.message : `Could not create ${kind}`);
    } finally {
      setCreating(false);
    }
  }, [kind, onSelect, setCandidates, value]);

  return (
    <CanonicalTypeahead
      label={kind[0].toUpperCase() + kind.slice(1)}
      value={value}
      selectedId={selectedId}
      options={options}
      loading={loading}
      failed={failed}
      required={required}
      creating={creating}
      createError={createError}
      onInputChange={(nextValue) => {
        setCreateError(null);
        onInputChange(nextValue);
      }}
      onSelect={(entity) => {
        setCreateError(null);
        onSelect(entity);
      }}
      onCreate={() => void createEntity()}
    />
  );
}

export function CountryCandidatePicker({
  value,
  selectedCode,
  onInputChange,
  onSelect,
}: {
  value: string;
  selectedCode: string | null;
  onInputChange: (value: string) => void;
  onSelect: (country: CountryCandidate) => void;
}) {
  const { candidates, loading, failed } = useCandidates<CountryCandidate>(
    value,
    "/api/normalization/countries?q=",
  );
  const options = useMemo(
    () => candidates.map((candidate) => ({ id: candidate.code, name: candidate.name })),
    [candidates],
  );

  return (
    <CanonicalTypeahead
      label="Country"
      value={value}
      selectedId={selectedCode}
      options={options}
      loading={loading}
      failed={failed}
      onInputChange={onInputChange}
      onSelect={(option) => {
        const country = candidates.find((candidate) => candidate.code === option.id);
        if (country) onSelect(country);
      }}
    />
  );
}
