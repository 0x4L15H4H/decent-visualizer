import uuid
from collections.abc import Callable
from typing import Any, cast

from app.db import Database
from app.lib.countries import country_name
from app.models.bean import Bean, BeanCreate, BeanPage, BeanUpdate
from app.models.entities import EntityKind
from app.storage.entities import EntityStorage

_ENTITY_FIELDS: dict[EntityKind, str] = {
    "roaster": "roaster_id",
    "producer": "producer_id",
    "farm": "farm_id",
    "variety": "variety_id",
    "process": "process_id",
}
_SELECT = """
SELECT b.*, r.id roaster_id_out, r.name roaster_name, p.id producer_id_out, p.name producer_name,
 f.id farm_id_out, f.name farm_name, v.id variety_id_out, v.name variety_name,
 pr.id process_id_out, pr.name process_name
FROM beans b JOIN canonical_entities r ON r.id=b.roaster_id
LEFT JOIN canonical_entities p ON p.id=b.producer_id LEFT JOIN canonical_entities f ON f.id=b.farm_id
LEFT JOIN canonical_entities v ON v.id=b.variety_id LEFT JOIN canonical_entities pr ON pr.id=b.process_id
"""


class BeanStorage:
    def __init__(self, database: Database) -> None:
        self._database: Database = database
        self._entity_storage: EntityStorage = EntityStorage(database)

    def list_page(
        self,
        *,
        page: int,
        page_size: int,
        q: str | None = None,
        sort_by: str = "created_at",
        descending: bool = True,
    ) -> BeanPage:
        rows = [self._to_model(dict(row)) for row in self._database.connection().execute(_SELECT)]
        if q:
            terms = q.lower().split()
            rows = [bean for bean in rows if all(term in self._searchable(bean) for term in terms)]
        sorters: dict[str, Callable[[Bean], str]] = {
            "name": lambda bean: bean.name.lower(),
            "roaster": lambda bean: bean.roaster.name.lower(),
            "country": lambda bean: (bean.country.name if bean.country else "").lower(),
            "variety": lambda bean: (bean.variety.name if bean.variety else "").lower(),
            "process": lambda bean: (bean.process.name if bean.process else "").lower(),
            "notes": lambda bean: (bean.notes or "").lower(),
            "created_at": lambda bean: bean.created_at.isoformat(),
        }
        rows.sort(key=sorters.get(sort_by, sorters["created_at"]), reverse=descending)
        total, offset = len(rows), (page - 1) * page_size
        return BeanPage(
            items=rows[offset : offset + page_size], total=total, page=page, page_size=page_size
        )

    def get(self, bean_id: str) -> Bean | None:
        row = (
            self._database.connection().execute(_SELECT + " WHERE b.id = ?", (bean_id,)).fetchone()
        )
        return self._to_model(dict(row)) if row else None

    def create(self, data: BeanCreate) -> Bean:
        self._validate_entity_ids(data.model_dump())
        bean_id, values = str(uuid.uuid4()), data.model_dump(mode="json")
        columns, marks = list(values), ",".join("?" for _ in values)
        connection = self._database.connection()
        connection.execute(
            f"INSERT INTO beans(id,{','.join(columns)},created_at) VALUES (?,{marks},strftime('%Y-%m-%dT%H:%M:%fZ','now'))",
            (bean_id, *values.values()),
        )
        connection.commit()
        return self.get(bean_id)  # pyright: ignore[reportReturnType]

    def update(self, bean_id: str, data: BeanUpdate) -> Bean | None:
        updates = data.model_dump(mode="json", exclude_unset=True)
        if not updates:
            return self.get(bean_id)
        self._validate_entity_ids(updates)
        connection = self._database.connection()
        result = connection.execute(
            f"UPDATE beans SET {', '.join(f'{key} = ?' for key in updates)} WHERE id = ?",
            (*updates.values(), bean_id),
        )
        connection.commit()
        return self.get(bean_id) if result.rowcount else None

    def delete(self, bean_id: str) -> bool:
        connection = self._database.connection()
        result = connection.execute("DELETE FROM beans WHERE id = ?", (bean_id,))
        connection.commit()
        return result.rowcount > 0

    def _validate_entity_ids(self, values: dict[str, Any]) -> None:
        if values.get("roaster_id") is None and "roaster_id" in values:
            raise ValueError("A bean must reference a roaster entity")
        country_code = cast(str | None, values.get("country_code"))
        if country_code is not None and country_name(country_code) is None:
            raise ValueError("Unknown country code")
        self._entity_storage.validate_references(
            {
                kind: cast(str | None, values[field])
                for kind, field in _ENTITY_FIELDS.items()
                if field in values
            }
        )

    @staticmethod
    def _searchable(bean: Bean) -> str:
        return " ".join(
            filter(
                None,
                [
                    bean.name,
                    bean.roaster.name,
                    bean.producer.name if bean.producer else None,
                    bean.farm.name if bean.farm else None,
                    bean.country.name if bean.country else None,
                    bean.variety.name if bean.variety else None,
                    bean.process.name if bean.process else None,
                    bean.notes,
                ],
            )
        ).lower()

    @staticmethod
    def _to_model(row: dict[str, Any]) -> Bean:
        country_code = row.get("country_code")
        country = (
            {"code": country_code, "name": country_name(country_code)} if country_code else None
        )

        def entity(prefix: str) -> dict[str, str] | None:
            return (
                {"id": row[f"{prefix}_id_out"], "name": row[f"{prefix}_name"]}
                if row.get(f"{prefix}_id_out")
                else None
            )

        return Bean.model_validate(
            {
                **row,
                "roaster": entity("roaster"),
                "producer": entity("producer"),
                "farm": entity("farm"),
                "variety": entity("variety"),
                "process": entity("process"),
                "country": country,
            }
        )
