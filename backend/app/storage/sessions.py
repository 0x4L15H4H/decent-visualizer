import uuid
from typing import Any

from app.db import Database


class SessionStorage:
    def __init__(self, database: Database) -> None:
        self._database: Database = database

    def create(self, user_id: str) -> dict[str, Any]:
        session_id = str(uuid.uuid4())
        connection = self._database.connection()
        connection.execute(
            """INSERT INTO sessions(id,user_id,created_at,expires_at)
            VALUES (?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'),
            strftime('%Y-%m-%dT%H:%M:%fZ','now','+30 days'))""",
            (session_id, user_id),
        )
        connection.commit()
        return self.get(session_id)  # pyright: ignore[reportReturnType]

    def get(self, session_id: str) -> dict[str, Any] | None:
        row = (
            self._database.connection()
            .execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            .fetchone()
        )
        return dict(row) if row else None

    def delete(self, session_id: str) -> bool:
        connection = self._database.connection()
        result = connection.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        connection.commit()
        return result.rowcount > 0

    def delete_expired(self, session_id: str) -> None:
        self.delete(session_id)
