import { Combobox } from "@base-ui/react/combobox";
import { useMemo } from "react";

export interface TypeaheadOption {
  id: string;
  name: string;
}

const CREATE_VALUE = "__create_canonical_entity__";

function TypeaheadPopup({
  options,
  canCreate,
  creating,
  loading,
  failed,
  value,
}: {
  options: TypeaheadOption[];
  canCreate: boolean;
  creating: boolean;
  loading: boolean;
  failed: boolean;
  value: string;
}) {
  return (
    <Combobox.Portal>
      <Combobox.Positioner className="z-50" sideOffset={4} align="start">
        <Combobox.Popup className="max-h-64 w-[var(--anchor-width)] overflow-hidden rounded-md border border-border-default bg-bg-surface shadow-xl">
          <Combobox.List className="max-h-64 overflow-y-auto p-1">
            {!loading &&
              options.map((option) => (
                <Combobox.Item
                  key={option.id}
                  value={option.id}
                  className="flex min-h-9 cursor-default items-center justify-between rounded px-2.5 py-2 text-sm text-text-secondary outline-none data-[highlighted]:bg-bg-raised data-[highlighted]:text-text-primary"
                >
                  <span className="min-w-0 truncate">{option.name}</span>
                  <Combobox.ItemIndicator className="ml-3 text-success">✓</Combobox.ItemIndicator>
                </Combobox.Item>
              ))}
            {canCreate && (
              <Combobox.Item
                value={CREATE_VALUE}
                disabled={creating}
                className="flex min-h-9 cursor-default items-center rounded px-2.5 py-2 text-sm text-accent outline-none data-[highlighted]:bg-bg-raised disabled:opacity-50"
              >
                {creating ? "Creating..." : `Create "${value.trim()}"`}
              </Combobox.Item>
            )}
            {!loading && !canCreate && options.length === 0 && (
              <Combobox.Empty className="px-2.5 py-3 text-sm text-text-muted">
                {failed ? "Search unavailable" : "No matches"}
              </Combobox.Empty>
            )}
          </Combobox.List>
        </Combobox.Popup>
      </Combobox.Positioner>
    </Combobox.Portal>
  );
}

export function CanonicalTypeahead({
  label,
  value,
  selectedId,
  options,
  loading,
  failed,
  required,
  creating = false,
  createError,
  onInputChange,
  onSelect,
  onCreate,
}: {
  label: string;
  value: string;
  selectedId: string | null;
  options: TypeaheadOption[];
  loading: boolean;
  failed: boolean;
  required?: boolean;
  creating?: boolean;
  createError?: string | null;
  onInputChange: (value: string) => void;
  onSelect: (option: TypeaheadOption) => void;
  onCreate?: () => void;
}) {
  const canCreate = Boolean(onCreate && value.trim() && !selectedId);
  const itemIds = useMemo(
    () => [...options.map((option) => option.id), ...(canCreate ? [CREATE_VALUE] : [])],
    [canCreate, options],
  );
  const status = loading
    ? `Searching ${label.toLowerCase()}...`
    : failed
      ? `Could not search ${label.toLowerCase()}`
      : `${options.length} ${label.toLowerCase()} option${options.length === 1 ? "" : "s"}`;

  return (
    <Combobox.Root<string>
      items={itemIds}
      filteredItems={itemIds}
      filter={null}
      value={selectedId}
      inputValue={value}
      openOnInputClick
      autoHighlight
      onInputValueChange={(nextValue, details) => {
        if (details.reason === "input-change" || details.reason === "input-clear") {
          onInputChange(nextValue);
        }
      }}
      onValueChange={(nextId) => {
        if (!nextId) return;
        if (nextId === CREATE_VALUE) return onCreate?.();
        const option = options.find((candidate) => candidate.id === nextId);
        if (option) onSelect(option);
      }}
    >
      <div className="flex min-w-0 flex-col gap-1">
        <Combobox.Label className="text-xs font-medium text-text-secondary">
          {label}
          {required ? " *" : ""}
        </Combobox.Label>
        <Combobox.InputGroup
          className={`flex h-9 min-w-0 items-center rounded-md border bg-bg-raised focus-within:ring-1 focus-within:ring-accent ${
            selectedId ? "border-success/60" : "border-border-default"
          }`}
        >
          <Combobox.Input
            required={required}
            placeholder={`Search ${label.toLowerCase()}`}
            className="h-full min-w-0 flex-1 bg-transparent px-3 text-sm text-text-primary outline-none placeholder:text-text-muted"
          />
          {(loading || creating) && (
            <span className="px-2 text-xs text-text-muted" aria-hidden="true">
              ...
            </span>
          )}
          {!loading && !creating && selectedId && (
            <span className="px-2 text-sm text-success" title="Canonical entity selected">
              ✓
            </span>
          )}
          <Combobox.Icon className="pr-3 text-xs text-text-muted">⌄</Combobox.Icon>
        </Combobox.InputGroup>
        <Combobox.Status className="sr-only">{status}</Combobox.Status>
        {createError && <span className="text-xs text-destructive">{createError}</span>}
      </div>
      <TypeaheadPopup
        options={options}
        canCreate={canCreate}
        creating={creating}
        loading={loading}
        failed={failed}
        value={value}
      />
    </Combobox.Root>
  );
}
