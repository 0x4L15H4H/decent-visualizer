import uuid
from typing import Any

from app.db import Database
from app.models.auth import UserResponse


class UserStorage:
    def __init__(self, database: Database) -> None:
        self._database: Database = database

    def create(
        self, email: str, password_hash: str, display_name: str | None = None
    ) -> UserResponse:
        user_id = str(uuid.uuid4())
        connection = self._database.connection()
        connection.execute(
            """INSERT INTO users(id,email,password_hash,display_name,created_at)
            VALUES (?,?,?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now'))""",
            (user_id, email, password_hash, display_name),
        )
        connection.commit()
        return self.get_by_id(user_id)  # pyright: ignore[reportReturnType]

    def get_by_email(self, email: str) -> dict[str, Any] | None:
        row = (
            self._database.connection()
            .execute("SELECT * FROM users WHERE email = ?", (email,))
            .fetchone()
        )
        return dict(row) if row else None

    def get_by_id(self, user_id: str) -> UserResponse | None:
        row = (
            self._database.connection()
            .execute("SELECT id,email,display_name,created_at FROM users WHERE id = ?", (user_id,))
            .fetchone()
        )
        return UserResponse.model_validate(dict(row)) if row else None
