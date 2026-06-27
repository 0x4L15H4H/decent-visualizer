import uuid
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
_BEAN_SELECT = """
    id,
    name,
    country_code,
    roast_level,
    roast_date,
    notes,
    created_at,
    roaster:canonical_entities!beans_roaster_id_fkey(id,name),
    producer:canonical_entities!beans_producer_id_fkey(id,name),
    farm:canonical_entities!beans_farm_id_fkey(id,name),
    variety:canonical_entities!beans_variety_id_fkey(id,name),
    process:canonical_entities!beans_process_id_fkey(id,name)
"""


class BeanStorage:
    _table: SyncRequestBuilder
    _entity_storage: EntityStorage

    def __init__(self, client: Client) -> None:
        self._table = client.table("beans")
        self._entity_storage = EntityStorage(client)

    def list(self) -> list[Bean]:
        response = self._table.select(_BEAN_SELECT).order("created_at", desc=True).execute()
        return [
            self._to_model(row) for row in cast(list[dict[str, Any]], response.data)
        ]

    def get(self, bean_id: str) -> Bean | None:
        response = self._table.select(_BEAN_SELECT).eq("id", bean_id).execute()
        if not response.data:
            return None
        return self._to_model(cast(dict[str, Any], response.data[0]))

    def create(self, data: BeanCreate) -> Bean:
        self._validate_entity_ids(data.model_dump())
        bean_id = str(uuid.uuid4())
        row = {"id": bean_id, **data.model_dump(mode="json")}
        self._table.insert(row).execute()
        bean = self.get(bean_id)
        if bean is None:
            raise RuntimeError("Created bean could not be read")
        return bean

    def update(self, bean_id: str, data: BeanUpdate) -> Bean | None:
        updates = data.model_dump(mode="json", exclude_unset=True)
        if not updates:
            return self.get(bean_id)
        self._validate_entity_ids(updates)
        response = self._table.update(updates).eq("id", bean_id).execute()
        if not response.data:
            return None
        return self.get(bean_id)

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

    @staticmethod
    def _to_model(row: dict[str, Any]) -> Bean:
        country_code = cast(str | None, row.get("country_code"))
        country = (
            {"code": country_code, "name": country_name(country_code)}
            if country_code is not None
            else None
        )
        return Bean.model_validate({**row, "country": country})
