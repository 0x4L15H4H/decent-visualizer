from typing import Any, cast

from postgrest._sync.request_builder import SyncRequestBuilder
from postgrest.types import JSON

from app.models.shot import ShotUpload, ShotUploadCreate, ShotUploadUpdate
from supabase import Client


class ShotStorage:
    _table: SyncRequestBuilder

    def __init__(self, client: Client) -> None:
        self._table = client.table("shots")

    def list(self) -> list[ShotUpload]:
        response = self._table.select("*").order("timestamp", desc=True).execute()
        return [self._to_model(row) for row in response.data]

    def get(self, shot_id: str) -> ShotUpload | None:
        response = self._table.select("*").eq("id", shot_id).execute()
        if not response.data:
            return None
        return self._to_model(response.data[0])

    def create(self, shot_id: str, data: ShotUploadCreate) -> ShotUpload:
        row = {
            "id": shot_id,
            **data.model_dump(mode="json"),
        }
        response = self._table.insert(row).execute()
        return self._to_model(response.data[0])

    def update(self, shot_id: str, data: ShotUploadUpdate) -> ShotUpload | None:
        updates = data.model_dump(mode="json", exclude_unset=True)
        if not updates:
            return self.get(shot_id)
        response = self._table.update(updates).eq("id", shot_id).execute()
        if not response.data:
            return None
        return self._to_model(response.data[0])

    def delete(self, shot_id: str) -> bool:
        response = self._table.delete().eq("id", shot_id).execute()
        return len(response.data) > 0

    @staticmethod
    def _to_model(row: JSON) -> ShotUpload:
        record = cast(dict[str, Any], row)
        return ShotUpload.model_validate({k: v for k, v in record.items() if k != "created_at"})
