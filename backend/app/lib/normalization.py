from pydantic_ai import ModelRetry

from app.models.bean import CanonicalSelection
from app.models.entities import NormalizationKind


def validate_entity_resolution(
    kind: NormalizationKind,
    value: CanonicalSelection,
    candidates_by_kind: dict[NormalizationKind, dict[str, str]] | None,
) -> None:
    candidates = (candidates_by_kind or {}).get(kind)
    if candidates is None:
        raise ModelRetry(f"Call find_normalization_candidates before returning {kind}.")
    if value.resolution == "matched":
        if value.canonical_id is None or candidates.get(value.canonical_id) != value.name:
            raise ModelRetry(
                f"Set {kind} canonical_id and name to one exact candidate, or propose a new entity."
            )
        return
    if kind == "country":
        raise ModelRetry("Countries must match the canonical ISO country list or be null.")
    if value.canonical_id is not None:
        raise ModelRetry(f"A proposed {kind} must have a null canonical_id.")
    if value.name in candidates.values():
        raise ModelRetry(f"{kind} matches an existing candidate; return it as matched.")
