import {
  useCallback,
  useEffect,
  useState,
  type Dispatch,
  type FormEvent,
  type SetStateAction,
} from "react";
import { CountryCandidatePicker, EntityCandidatePicker } from "./NormalizationCandidatePicker";
import { PhotoExtractButton, type ExtractedBean } from "./PhotoExtractButton";
import type { BeanFormValues } from "../types/bean";

const inputClass =
  "w-full rounded-md border border-border-default bg-bg-raised px-3 py-1.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-accent";

const buttonClass =
  "rounded-md border border-border-default bg-bg-raised px-3 py-1.5 text-sm font-medium text-text-primary hover:bg-white/10 disabled:opacity-50";

function mergeExtracted(prev: BeanFormValues, data: ExtractedBean): BeanFormValues {
  return {
    ...prev,
    name: data.name ?? prev.name,
    roaster: data.roaster?.name ?? prev.roaster,
    roasterId: data.roaster ? data.roaster.canonical_id : prev.roasterId,
    producer: data.producer?.name ?? prev.producer,
    producerId: data.producer ? data.producer.canonical_id : prev.producerId,
    farm: data.farm?.name ?? prev.farm,
    farmId: data.farm ? data.farm.canonical_id : prev.farmId,
    country: data.country?.name ?? prev.country,
    countryCode: data.country ? data.country.canonical_id : prev.countryCode,
    variety: data.variety?.name ?? prev.variety,
    varietyId: data.variety ? data.variety.canonical_id : prev.varietyId,
    process: data.process?.name ?? prev.process,
    processId: data.process ? data.process.canonical_id : prev.processId,
    notes: data.notes ?? prev.notes,
  };
}

function findUnresolved(values: BeanFormValues) {
  return [
    ["roaster", values.roaster, values.roasterId],
    ["producer", values.producer, values.producerId],
    ["farm", values.farm, values.farmId],
    ["country", values.country, values.countryCode],
    ["variety", values.variety, values.varietyId],
    ["process", values.process, values.processId],
  ].find(([, name, id]) => Boolean(name) && !id);
}

function BeanIdentityFields({
  values,
  setValues,
}: {
  values: BeanFormValues;
  setValues: Dispatch<SetStateAction<BeanFormValues>>;
}) {
  const entityField = (
    kind: "roaster" | "producer" | "farm" | "variety" | "process",
    idField: "roasterId" | "producerId" | "farmId" | "varietyId" | "processId",
    required = false,
  ) => (
    <input
      type="text"
      placeholder={`${kind[0].toUpperCase()}${kind.slice(1)}${required ? " *" : ""}`}
      required={required}
      value={values[kind]}
      onChange={(event) =>
        setValues((prev) => ({ ...prev, [kind]: event.target.value, [idField]: null }))
      }
      className={inputClass}
    />
  );
  const picker = (
    kind: "roaster" | "producer" | "farm" | "variety" | "process",
    idField: "roasterId" | "producerId" | "farmId" | "varietyId" | "processId",
  ) => (
    <EntityCandidatePicker
      kind={kind}
      value={values[kind]}
      selectedId={values[idField]}
      onSelect={(entity) =>
        setValues((prev) => ({ ...prev, [kind]: entity.name, [idField]: entity.id }))
      }
    />
  );
  return (
    <>
      <div className="grid grid-cols-2 gap-3">
        <input
          type="text"
          placeholder="Name *"
          required
          value={values.name}
          onChange={(event) => setValues((prev) => ({ ...prev, name: event.target.value }))}
          className={inputClass}
        />
        {entityField("roaster", "roasterId", true)}
        {entityField("producer", "producerId")}
        {entityField("farm", "farmId")}
        <input
          type="text"
          placeholder="Country"
          value={values.country}
          onChange={(event) =>
            setValues((prev) => ({ ...prev, country: event.target.value, countryCode: null }))
          }
          className={inputClass}
        />
        {entityField("variety", "varietyId")}
        {entityField("process", "processId")}
      </div>
      <div className="flex flex-col gap-1">
        {picker("roaster", "roasterId")}
        {picker("producer", "producerId")}
        {picker("farm", "farmId")}
        <CountryCandidatePicker
          value={values.country}
          selectedCode={values.countryCode}
          onSelect={(country) =>
            setValues((prev) => ({ ...prev, country: country.name, countryCode: country.code }))
          }
        />
        {picker("variety", "varietyId")}
        {picker("process", "processId")}
      </div>
    </>
  );
}

export function BeanForm({
  initialValues,
  submitLabel,
  busyLabel,
  onSubmit,
  onCancel,
}: {
  initialValues: BeanFormValues;
  submitLabel: string;
  busyLabel: string;
  onSubmit: (values: BeanFormValues) => Promise<void>;
  onCancel?: () => void;
}) {
  const [values, setValues] = useState(initialValues);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    setValues(initialValues);
    setError(null);
  }, [initialValues]);

  const updateValue = useCallback((field: keyof BeanFormValues, value: string) => {
    setValues((prev) => ({ ...prev, [field]: value }));
  }, []);

  const handleExtracted = useCallback((data: ExtractedBean) => {
    setValues((prev) => mergeExtracted(prev, data));
  }, []);

  const handleSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();
      setError(null);
      const unresolved = findUnresolved(values);
      if (unresolved) {
        setError(`Select an existing ${unresolved[0]} or create it before saving.`);
        return;
      }
      setSubmitting(true);
      try {
        await onSubmit(values);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Something went wrong");
      } finally {
        setSubmitting(false);
      }
    },
    [onSubmit, values],
  );

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <PhotoExtractButton onExtracted={handleExtracted} />
      <BeanIdentityFields values={values} setValues={setValues} />
      <textarea
        placeholder="Flavor notes"
        rows={2}
        value={values.notes}
        onChange={(e) => updateValue("notes", e.target.value)}
        className={inputClass + " resize-none"}
      />
      {error && <p className="text-sm text-destructive">{error}</p>}
      <div className="flex justify-end gap-2">
        {onCancel && (
          <button type="button" onClick={onCancel} className={buttonClass}>
            Cancel
          </button>
        )}
        <button type="submit" disabled={submitting} className={buttonClass}>
          {submitting ? busyLabel : submitLabel}
        </button>
      </div>
    </form>
  );
}
