import builtins
import uuid
from collections.abc import Sequence
from typing import Any, cast

from postgrest._sync.request_builder import SyncRequestBuilder

from app.lib.countries import country_name
from app.models.bean import Bean, BeanCreate, BeanUpdate
from app.models.entities import EntityKind
from app.storage.entities import EntityStorage
from supabase import Client

_ENTITY_FIELDS: dict[EntityKind, str] = {
    "roaster": "roaster_id",
    "producer": "producer_id",
    "farm": "farm_id",
    "variety": "variety_id",
    "process": "process_id",
}


class BeanStorage:
    _table: SyncRequestBuilder
    _entity_table: SyncRequestBuilder
    _entity_storage: EntityStorage

    def __init__(self, client: Client) -> None:
        self._table = client.table("beans")
        self._entity_table = client.table("canonical_entities")
        self._entity_storage = EntityStorage(client)

    def list(self) -> list[Bean]:
        response = self._table.select("*").order("created_at", desc=True).execute()
        return self._to_models(cast(list[dict[str, Any]], response.data))

    def get(self, bean_id: str) -> Bean | None:
        response = self._table.select("*").eq("id", bean_id).execute()
        if not response.data:
            return None
        return self._to_models(cast(list[dict[str, Any]], response.data))[0]

    def create(self, data: BeanCreate) -> Bean:
        self._validate_entity_ids(data.model_dump())
        bean_id = str(uuid.uuid4())
        row = {"id": bean_id, **data.model_dump(mode="json")}
        response = self._table.insert(row).execute()
        return self._to_models(cast(list[dict[str, Any]], response.data))[0]

    def update(self, bean_id: str, data: BeanUpdate) -> Bean | None:
        updates = data.model_dump(mode="json", exclude_unset=True)
        if not updates:
            return self.get(bean_id)
        self._validate_entity_ids(updates)
        response = self._table.update(updates).eq("id", bean_id).execute()
        if not response.data:
            return None
        return self._to_models(cast(list[dict[str, Any]], response.data))[0]

    def delete(self, bean_id: str) -> bool:
        response = self._table.delete().eq("id", bean_id).execute()
        return len(response.data) > 0

    def _validate_entity_ids(self, values: dict[str, Any]) -> None:
        if "roaster_id" in values and values["roaster_id"] is None:
            raise ValueError("A bean must reference a roaster entity")
        country_code = cast(str | None, values.get("country_code"))
        if country_code is not None and country_name(country_code) is None:
            raise ValueError("Unknown country code")
        references: dict[EntityKind, str | None] = {
            kind: cast(str | None, values.get(field))
            for kind, field in _ENTITY_FIELDS.items()
            if field in values
        }
        self._entity_storage.validate_references(references)

    def _to_models(self, rows: Sequence[dict[str, Any]]) -> builtins.list[Bean]:
        typed_rows = builtins.list(rows)
        entity_ids = {
            str(row[field])
            for row in typed_rows
            for field in _ENTITY_FIELDS.values()
            if row.get(field)
        }
        names_by_id: dict[str, str] = {}
        if entity_ids:
            response = self._entity_table.select("id,name").in_("id", list(entity_ids)).execute()
            names_by_id = {
                str(row["id"]): str(row["name"])
                for row in cast(list[dict[str, Any]], response.data)
            }

        beans: list[Bean] = []
        for row in typed_rows:
            hydrated = dict(row)
            for kind, field in _ENTITY_FIELDS.items():
                entity_id = hydrated.get(field)
                hydrated[kind] = names_by_id.get(str(entity_id)) if entity_id else None
            hydrated["country"] = country_name(cast(str | None, hydrated.get("country_code")))
            beans.append(Bean.model_validate(hydrated))
        return beans
