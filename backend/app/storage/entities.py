import re
import unicodedata
import uuid
from difflib import SequenceMatcher
from typing import Any, cast

from postgrest._sync.request_builder import SyncRequestBuilder

from app.models.entities import (
    AliasSource,
    CanonicalEntity,
    EntityAlias,
    EntityCreate,
    EntityKind,
    EntityUpdate,
    NormalizationCandidate,
)
from supabase import Client


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"[^a-z0-9]+", " ", value.lower())
    return " ".join(value.split())


def _similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0
    if left in right or right in left:
        return 0.9
    return SequenceMatcher(a=left, b=right).ratio()


class EntityStorage:
    _entities: SyncRequestBuilder
    _aliases: SyncRequestBuilder

    def __init__(self, client: Client) -> None:
        self._entities = client.table("canonical_entities")
        self._aliases = client.table("entity_aliases")

    def list_entities(
        self, *, kind: EntityKind | None = None, q: str | None = None
    ) -> list[CanonicalEntity]:
        query = self._entities.select("*").order("name")
        if kind:
            query = query.eq("kind", kind)
        rows = [cast(dict[str, Any], row) for row in query.execute().data]
        if q:
            normalized_query = _normalize(q)
            rows = [
                row
                for row in rows
                if normalized_query in _normalize(str(row.get("name", "")))
                or _similarity(normalized_query, _normalize(str(row.get("name", "")))) >= 0.7
            ]
        return self._with_aliases(rows)

    def get(self, entity_id: str) -> CanonicalEntity | None:
        response = self._entities.select("*").eq("id", entity_id).execute()
        if not response.data:
            return None
        return self._with_aliases([cast(dict[str, Any], response.data[0])])[0]

    def create(self, data: EntityCreate) -> CanonicalEntity:
        entity_id = str(uuid.uuid4())
        row = {"id": entity_id, **data.model_dump(mode="json")}
        response = self._entities.insert(row).execute()
        return self._with_aliases([cast(dict[str, Any], response.data[0])])[0]

    def update(self, entity_id: str, data: EntityUpdate) -> CanonicalEntity | None:
        updates = data.model_dump(mode="json", exclude_unset=True)
        if not updates:
            return self.get(entity_id)
        response = self._entities.update(updates).eq("id", entity_id).execute()
        if not response.data:
            return None
        return self._with_aliases([cast(dict[str, Any], response.data[0])])[0]

    def add_alias(self, *, entity_id: str, alias: str, source: AliasSource) -> EntityAlias | None:
        if self.get(entity_id) is None:
            return None
        alias_id = str(uuid.uuid4())
        response = self._aliases.insert(
            {
                "id": alias_id,
                "entity_id": entity_id,
                "alias": alias,
                "source": source,
            }
        ).execute()
        return EntityAlias.model_validate(cast(dict[str, Any], response.data[0]))

    def delete_alias(self, *, entity_id: str, alias_id: str) -> bool:
        response = self._aliases.delete().eq("entity_id", entity_id).eq("id", alias_id).execute()
        return len(response.data) > 0

    def candidates(
        self, *, kind: EntityKind, value: str, limit: int = 8
    ) -> list[NormalizationCandidate]:
        normalized_value = _normalize(value)
        entities = self.list_entities(kind=kind)
        scored: list[NormalizationCandidate] = []
        for entity in entities:
            names = [entity.name, *[alias.alias for alias in entity.aliases]]
            best_score = 0.0
            best_reason = "name_similarity"
            for name in names:
                score = _similarity(normalized_value, _normalize(name))
                if score > best_score:
                    best_score = score
                    best_reason = "alias_match" if name != entity.name else "name_match"
            if best_score >= 0.45:
                scored.append(
                    NormalizationCandidate(
                        id=entity.id,
                        kind=entity.kind,
                        canonical_name=entity.name,
                        aliases=[alias.alias for alias in entity.aliases],
                        score=round(best_score, 4),
                        match_reason=best_reason,
                    )
                )
        return sorted(scored, key=lambda candidate: candidate.score, reverse=True)[:limit]

    def validate_references(self, references: dict[EntityKind, str | None]) -> None:
        entity_ids = [entity_id for entity_id in references.values() if entity_id is not None]
        if not entity_ids:
            return
        response = self._entities.select("id,kind").in_("id", entity_ids).execute()
        kinds_by_id = {
            str(row["id"]): str(row["kind"]) for row in cast(list[dict[str, Any]], response.data)
        }
        for expected_kind, entity_id in references.items():
            if entity_id is None:
                continue
            actual_kind = kinds_by_id.get(entity_id)
            if actual_kind is None:
                raise ValueError(f"Unknown {expected_kind} entity ID")
            if actual_kind != expected_kind:
                raise ValueError(f"Entity {entity_id} is a {actual_kind}, not a {expected_kind}")

    def _with_aliases(self, rows: list[dict[str, Any]]) -> list[CanonicalEntity]:
        if not rows:
            return []
        entity_ids = [str(row["id"]) for row in rows]
        alias_response = self._aliases.select("*").in_("entity_id", entity_ids).execute()
        aliases_by_entity: dict[str, list[EntityAlias]] = {
            entity_id: [] for entity_id in entity_ids
        }
        for row in alias_response.data:
            alias = EntityAlias.model_validate(row)
            aliases_by_entity.setdefault(alias.entity_id, []).append(alias)

        entities: list[CanonicalEntity] = []
        for row in rows:
            entity = CanonicalEntity.model_validate(row)
            entity.aliases.extend(aliases_by_entity.get(entity.id, []))
            entities.append(entity)
        return entities
