from typing import Any, cast

from postgrest._sync.request_builder import SyncRequestBuilder
from postgrest.types import JSON

from app.models.shot import ShotSummary, ShotUpload, ShotUploadCreate, ShotUploadUpdate
from supabase import Client

# Lightweight projection for list views. The coffee name lives in the workflow
# JSON; selecting just that path avoids shipping the whole workflow/measurements.
_SUMMARY_SELECT = "id,timestamp,duration,coffee_name:workflow->context->>coffeeName"


class ShotStorage:
    _table: SyncRequestBuilder

    def __init__(self, client: Client) -> None:
        self._table = client.table("shots")

    def list(self) -> list[ShotSummary]:
        response = self._table.select(_SUMMARY_SELECT).order("timestamp", desc=True).execute()
        return [self._to_summary(row) for row in response.data]

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
        return ShotUpload.model_validate(cast(dict[str, Any], row))

    @staticmethod
    def _to_summary(row: JSON) -> ShotSummary:
        return ShotSummary.model_validate(cast(dict[str, Any], row))
