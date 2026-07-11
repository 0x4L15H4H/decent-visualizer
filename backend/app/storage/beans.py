import uuid
from typing import Any, cast

from postgrest._sync.request_builder import SyncRequestBuilder
from supabase import Client

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
    _client: Client
    _table: SyncRequestBuilder
    _entity_storage: EntityStorage

    def __init__(self, client: Client) -> None:
        self._client = client
        self._table = client.table("beans")
        self._entity_storage = EntityStorage(client)

    def list_page(
        self,
        *,
        page: int,
        page_size: int,
        q: str | None = None,
        sort_by: str = "created_at",
        descending: bool = True,
    ) -> BeanPage:
        offset = (page - 1) * page_size
        search_response = self._client.rpc(
            "search_bean_ids",
            {
                "p_query": q,
                "p_offset": offset,
                "p_limit": page_size,
                "p_sort_by": sort_by,
                "p_desc": descending,
            },
        ).execute()
        search_rows = cast(list[dict[str, Any]], search_response.data)
        ids = [str(row["id"]) for row in search_rows if row["id"] is not None]
        total = int(search_rows[0]["total_count"]) if search_rows else 0
        if not ids:
            return BeanPage(
                items=[],
                total=total,
                page=page,
                page_size=page_size,
            )

        bean_response = self._table.select(_BEAN_SELECT).in_("id", ids).execute()
        bean_rows = cast(list[dict[str, Any]], bean_response.data)
        beans_by_id = {str(row["id"]): self._to_model(row) for row in bean_rows}
        return BeanPage(
            items=[beans_by_id[bean_id] for bean_id in ids if bean_id in beans_by_id],
            total=total,
            page=page,
            page_size=page_size,
        )

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
