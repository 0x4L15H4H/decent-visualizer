from typing import Any, cast

from postgrest._sync.request_builder import SyncRequestBuilder
from postgrest.types import JSON
from supabase import Client

from app.models.auth import UserResponse


class UserStorage:
    _table: SyncRequestBuilder

    def __init__(self, client: Client) -> None:
        self._table = client.table("users")

    def create(
        self, email: str, password_hash: str, display_name: str | None = None
    ) -> UserResponse:
        row: dict[str, Any] = {"email": email, "password_hash": password_hash}
        if display_name is not None:
            row["display_name"] = display_name
        response = self._table.insert(row).execute()
        return self._to_model(response.data[0])

    def get_by_email(self, email: str) -> dict[str, Any] | None:
        response = self._table.select("*").eq("email", email).execute()
        if not response.data:
            return None
        return cast(dict[str, Any], response.data[0])

    def get_by_id(self, user_id: str) -> UserResponse | None:
        select = "id,email,display_name,created_at"
        response = self._table.select(select).eq("id", user_id).execute()
        if not response.data:
            return None
        return self._to_model(response.data[0])

    @staticmethod
    def _to_model(row: JSON) -> UserResponse:
        return UserResponse.model_validate(cast(dict[str, Any], row))
