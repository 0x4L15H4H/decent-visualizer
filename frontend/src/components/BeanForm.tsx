import { useCallback, useEffect, useState, type FormEvent } from "react";
import {
  CountryCandidatePicker,
  EntityCandidatePicker,
} from "./NormalizationCandidatePicker";
import { PhotoExtractButton, type ExtractedBean } from "./PhotoExtractButton";
import type { BeanFormValues } from "../types/bean";

const inputClass =
  "w-full rounded-md border border-border-default bg-bg-raised px-3 py-1.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-accent";

const buttonClass =
  "rounded-md border border-border-default bg-bg-raised px-3 py-1.5 text-sm font-medium text-text-primary hover:bg-white/10 disabled:opacity-50";

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
    setValues((prev) => ({
      name: data.name ?? prev.name,
      roaster: data.roaster ?? prev.roaster,
      producer: data.producer ?? prev.producer,
      farm: data.farm ?? prev.farm,
      country: data.country ?? prev.country,
      variety: data.variety ?? prev.variety,
      process: data.process ?? prev.process,
      notes: data.notes ?? prev.notes,
    }));
  }, []);

  const handleSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();
      setError(null);
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
      <div className="grid grid-cols-2 gap-3">
        <input type="text" placeholder="Name *" required value={values.name} onChange={(e) => updateValue("name", e.target.value)} className={inputClass} />
        <input type="text" placeholder="Roaster *" required value={values.roaster} onChange={(e) => updateValue("roaster", e.target.value)} className={inputClass} />
        <input type="text" placeholder="Producer" value={values.producer} onChange={(e) => updateValue("producer", e.target.value)} className={inputClass} />
        <input type="text" placeholder="Farm" value={values.farm} onChange={(e) => updateValue("farm", e.target.value)} className={inputClass} />
        <input type="text" placeholder="Country" value={values.country} onChange={(e) => updateValue("country", e.target.value)} className={inputClass} />
        <input type="text" placeholder="Variety" value={values.variety} onChange={(e) => updateValue("variety", e.target.value)} className={inputClass} />
        <input type="text" placeholder="Process" value={values.process} onChange={(e) => updateValue("process", e.target.value)} className={inputClass} />
      </div>
      <div className="flex flex-col gap-1">
        <EntityCandidatePicker kind="roaster" value={values.roaster} onSelect={(value) => updateValue("roaster", value)} />
        <EntityCandidatePicker kind="producer" value={values.producer} onSelect={(value) => updateValue("producer", value)} />
        <EntityCandidatePicker kind="farm" value={values.farm} onSelect={(value) => updateValue("farm", value)} />
        <CountryCandidatePicker value={values.country} onSelect={(value) => updateValue("country", value)} />
        <EntityCandidatePicker kind="variety" value={values.variety} onSelect={(value) => updateValue("variety", value)} />
        <EntityCandidatePicker kind="process" value={values.process} onSelect={(value) => updateValue("process", value)} />
      </div>
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
