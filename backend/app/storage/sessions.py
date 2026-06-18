from typing import Any, cast

from postgrest._sync.request_builder import SyncRequestBuilder

from supabase import Client


class SessionStorage:
    _table: SyncRequestBuilder

    def __init__(self, client: Client) -> None:
        self._table = client.table("sessions")

    def create(self, user_id: str) -> dict[str, Any]:
        row = {"user_id": user_id}
        response = self._table.insert(row).execute()
        return cast(dict[str, Any], response.data[0])

    def get(self, session_id: str) -> dict[str, Any] | None:
        response = self._table.select("*").eq("id", session_id).execute()
        if not response.data:
            return None
        return cast(dict[str, Any], response.data[0])

    def delete(self, session_id: str) -> bool:
        response = self._table.delete().eq("id", session_id).execute()
        return len(response.data) > 0

    def delete_expired(self, session_id: str) -> None:
        self._table.delete().eq("id", session_id).execute()
