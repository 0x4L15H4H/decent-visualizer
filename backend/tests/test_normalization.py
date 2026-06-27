from datetime import UTC, datetime

import pytest
from pydantic_ai import ModelRetry

from app.lib.countries import country_candidates, country_name
from app.lib.normalization import validate_entity_resolution
from app.models.bean import CanonicalSelection
from app.models.entities import (
    CanonicalEntity,
    EntityAlias,
    EntityKind,
    NormalizationKind,
)
from app.storage.entities import EntityStorage

NOW = datetime.now(UTC)


def canonical_entity(
    *,
    entity_id: str,
    name: str,
    kind: EntityKind = "process",
    aliases: list[str] | None = None,
) -> CanonicalEntity:
    return CanonicalEntity.model_validate(
        {
            "id": entity_id,
            "kind": kind,
            "name": name,
            "created_at": NOW,
            "updated_at": NOW,
            "aliases": [
                EntityAlias(
                    id=f"alias-{index}",
                    entity_id=entity_id,
                    alias=alias,
                    source="system",
                    created_at=NOW,
                )
                for index, alias in enumerate(aliases or [])
            ],
        }
    )


def candidate_storage(
    monkeypatch: pytest.MonkeyPatch, entities: list[CanonicalEntity]
) -> EntityStorage:
    storage = EntityStorage.__new__(EntityStorage)

    def list_entities(
        *, kind: EntityKind | None = None, q: str | None = None
    ) -> list[CanonicalEntity]:
        del kind, q
        return entities

    monkeypatch.setattr(storage, "list_entities", list_entities)
    return storage


def test_candidate_search_normalizes_case_punctuation_and_accents(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage = candidate_storage(
        monkeypatch,
        [
            canonical_entity(entity_id="best", name="Finca El Paraíso", kind="farm"),
            canonical_entity(entity_id="other", name="El Paraiso Coffee", kind="farm"),
        ],
    )

    candidates = storage.candidates(kind="farm", value="FINCA EL PARAISO")

    assert candidates[0].id == "best"
    assert candidates[0].score == 1
    assert candidates[0].match_reason == "name_match"


def test_candidate_search_uses_curated_aliases(monkeypatch: pytest.MonkeyPatch) -> None:
    storage = candidate_storage(
        monkeypatch,
        [
            canonical_entity(
                entity_id="anaerobic-natural",
                name="Anaerobic Natural",
                aliases=["Natural Anaerobic"],
            )
        ],
    )

    candidates = storage.candidates(kind="process", value="natural anaerobic")

    assert len(candidates) == 1
    assert candidates[0].id == "anaerobic-natural"
    assert candidates[0].score == 1
    assert candidates[0].match_reason == "alias_match"


def test_candidate_search_excludes_weak_matches(monkeypatch: pytest.MonkeyPatch) -> None:
    storage = candidate_storage(
        monkeypatch,
        [canonical_entity(entity_id="washed", name="Washed")],
    )

    assert storage.candidates(kind="process", value="carbonic maceration") == []


def test_country_candidates_resolve_codes_names_and_known_aliases() -> None:
    assert country_candidates("ET")[0].name == "Ethiopia"
    assert country_candidates("ethiopia")[0].code == "ET"
    assert country_candidates("Columbia")[0].code == "CO"
    assert country_name("et") == "Ethiopia"


def test_matched_resolution_must_use_an_exact_returned_candidate() -> None:
    candidates: dict[NormalizationKind, dict[str, str]] = {"process": {"process-id": "Washed"}}

    validate_entity_resolution(
        "process",
        CanonicalSelection(
            resolution="matched",
            canonical_id="process-id",
            name="Washed",
        ),
        candidates,
    )

    with pytest.raises(ModelRetry, match="exact candidate"):
        validate_entity_resolution(
            "process",
            CanonicalSelection(
                resolution="matched",
                canonical_id="invented-id",
                name="Washed",
            ),
            candidates,
        )


def test_existing_candidate_cannot_be_returned_as_a_proposal() -> None:
    with pytest.raises(ModelRetry, match="matches an existing candidate"):
        validate_entity_resolution(
            "process",
            CanonicalSelection(
                resolution="proposed",
                canonical_id=None,
                name="Washed",
            ),
            {"process": {"process-id": "Washed"}},
        )


def test_new_open_world_value_can_be_proposed() -> None:
    validate_entity_resolution(
        "process",
        CanonicalSelection(
            resolution="proposed",
            canonical_id=None,
            name="Thermal Shock",
        ),
        {"process": {"washed-id": "Washed"}},
    )


def test_resolution_requires_candidate_lookup() -> None:
    with pytest.raises(ModelRetry, match="Call find_normalization_candidates"):
        validate_entity_resolution(
            "farm",
            CanonicalSelection(
                resolution="proposed",
                canonical_id=None,
                name="Finca Nueva",
            ),
            None,
        )


def test_country_must_be_matched_or_null() -> None:
    with pytest.raises(ModelRetry, match="canonical ISO country list"):
        validate_entity_resolution(
            "country",
            CanonicalSelection(
                resolution="proposed",
                canonical_id=None,
                name="Atlantis",
            ),
            {"country": {}},
        )
