import uuid
from typing import Any, cast

from postgrest._sync.request_builder import SyncRequestBuilder
from postgrest.types import JSON

from app.models.bean import Bean, BeanCreate, BeanUpdate
from supabase import Client


class BeanStorage:
    _table: SyncRequestBuilder

    def __init__(self, client: Client) -> None:
        self._table = client.table("beans")

    def list(self) -> list[Bean]:
        response = self._table.select("*").order("created_at", desc=True).execute()
        return [self._to_model(row) for row in response.data]

    def get(self, bean_id: str) -> Bean | None:
        response = self._table.select("*").eq("id", bean_id).execute()
        if not response.data:
            return None
        return self._to_model(response.data[0])

    def create(self, data: BeanCreate) -> Bean:
        bean_id = str(uuid.uuid4())
        row = {"id": bean_id, **data.model_dump(mode="json")}
        response = self._table.insert(row).execute()
        return self._to_model(response.data[0])

    def update(self, bean_id: str, data: BeanUpdate) -> Bean | None:
        updates = data.model_dump(mode="json", exclude_unset=True)
        if not updates:
            return self.get(bean_id)
        response = self._table.update(updates).eq("id", bean_id).execute()
        if not response.data:
            return None
        return self._to_model(response.data[0])

    def delete(self, bean_id: str) -> bool:
        response = self._table.delete().eq("id", bean_id).execute()
        return len(response.data) > 0

    @staticmethod
    def _to_model(row: JSON) -> Bean:
        return Bean.model_validate(cast(dict[str, Any], row))
