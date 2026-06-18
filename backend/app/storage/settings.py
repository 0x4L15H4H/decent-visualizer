from typing import Any, cast

from postgrest._sync.request_builder import SyncRequestBuilder

from supabase import Client


class SettingsStorage:
    _table: SyncRequestBuilder

    def __init__(self, client: Client) -> None:
        self._table = client.table("settings")

    def get(self, key: str) -> Any:
        response = self._table.select("value").eq("key", key).execute()
        if not response.data:
            return None
        return cast(dict[str, Any], response.data[0])["value"]

    def set(self, key: str, value: Any) -> None:
        self._table.upsert({"key": key, "value": value}).execute()
