import json
import re
import unicodedata
import uuid
from difflib import SequenceMatcher

from app.db import Database
from app.models.entities import (
    AliasSource,
    CanonicalEntity,
    EntityAlias,
    EntityCreate,
    EntityKind,
    EntityUpdate,
    NormalizationCandidate,
)


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
    def __init__(self, database: Database) -> None:
        self._database: Database = database

    def list_entities(
        self, *, kind: EntityKind | None = None, q: str | None = None
    ) -> list[CanonicalEntity]:
        sql = "SELECT * FROM canonical_entities"
        values: tuple[str, ...] = ()
        if kind:
            sql += " WHERE kind = ?"
            values = (kind,)
        rows = [
            dict(row) for row in self._database.connection().execute(sql + " ORDER BY name", values)
        ]
        if q:
            normalized_query = _normalize(q)
            rows = [
                row
                for row in rows
                if normalized_query in _normalize(row["name"])
                or _similarity(normalized_query, _normalize(row["name"])) >= 0.7
            ]
        return self._with_aliases(rows)

    def get(self, entity_id: str) -> CanonicalEntity | None:
        row = (
            self._database.connection()
            .execute("SELECT * FROM canonical_entities WHERE id = ?", (entity_id,))
            .fetchone()
        )
        return self._with_aliases([dict(row)])[0] if row else None

    def create(self, data: EntityCreate) -> CanonicalEntity:
        entity_id = str(uuid.uuid4())
        connection = self._database.connection()
        connection.execute(
            """INSERT INTO canonical_entities(id,kind,name,country_code,metadata,created_at,updated_at)
            VALUES (?,?,?,?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'))""",
            (entity_id, data.kind, data.name, data.country_code, json.dumps(data.metadata)),
        )
        connection.commit()
        return self.get(entity_id)  # pyright: ignore[reportReturnType]

    def update(self, entity_id: str, data: EntityUpdate) -> CanonicalEntity | None:
        updates = data.model_dump(mode="json", exclude_unset=True)
        if not updates:
            return self.get(entity_id)
        if "metadata" in updates:
            updates["metadata"] = json.dumps(updates["metadata"])
        assignments = ", ".join(f"{key} = ?" for key in updates)
        connection = self._database.connection()
        result = connection.execute(
            f"UPDATE canonical_entities SET {assignments}, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = ?",
            (*updates.values(), entity_id),
        )
        connection.commit()
        return self.get(entity_id) if result.rowcount else None

    def add_alias(self, *, entity_id: str, alias: str, source: AliasSource) -> EntityAlias | None:
        if self.get(entity_id) is None:
            return None
        alias_id = str(uuid.uuid4())
        connection = self._database.connection()
        connection.execute(
            """INSERT INTO entity_aliases(id,entity_id,alias,source,created_at)
            VALUES (?,?,?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now'))""",
            (alias_id, entity_id, alias, source),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM entity_aliases WHERE id = ?", (alias_id,)
        ).fetchone()
        return EntityAlias.model_validate(dict(row))

    def delete_alias(self, *, entity_id: str, alias_id: str) -> bool:
        connection = self._database.connection()
        result = connection.execute(
            "DELETE FROM entity_aliases WHERE entity_id = ? AND id = ?", (entity_id, alias_id)
        )
        connection.commit()
        return result.rowcount > 0

    def candidates(
        self, *, kind: EntityKind, value: str, limit: int = 8
    ) -> list[NormalizationCandidate]:
        normalized_value = _normalize(value)
        scored: list[NormalizationCandidate] = []
        for entity in self.list_entities(kind=kind):
            names = [entity.name, *[alias.alias for alias in entity.aliases]]
            best_score, best_reason = 0.0, "name_similarity"
            for name in names:
                score = _similarity(normalized_value, _normalize(name))
                if score > best_score:
                    best_score, best_reason = (
                        score,
                        "alias_match" if name != entity.name else "name_match",
                    )
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
        for expected_kind, entity_id in references.items():
            if entity_id is None:
                continue
            row = (
                self._database.connection()
                .execute("SELECT kind FROM canonical_entities WHERE id = ?", (entity_id,))
                .fetchone()
            )
            if row is None:
                raise ValueError(f"Unknown {expected_kind} entity ID")
            if row["kind"] != expected_kind:
                raise ValueError(f"Entity {entity_id} is a {row['kind']}, not a {expected_kind}")

    def _with_aliases(self, rows: list[dict[str, object]]) -> list[CanonicalEntity]:
        if not rows:
            return []
        placeholders = ",".join("?" for _ in rows)
        ids = [str(row["id"]) for row in rows]
        aliases_by_entity: dict[str, list[EntityAlias]] = {entity_id: [] for entity_id in ids}
        for alias in self._database.connection().execute(
            f"SELECT * FROM entity_aliases WHERE entity_id IN ({placeholders})", ids
        ):
            value = EntityAlias.model_validate(dict(alias))
            aliases_by_entity[value.entity_id].append(value)
        return [
            CanonicalEntity.model_validate(
                {
                    **row,
                    "metadata": json.loads(str(row["metadata"])),
                    "aliases": aliases_by_entity[str(row["id"])],
                }
            )
            for row in rows
        ]
