import json
from typing import Any

from app.db import Database


class SettingsStorage:
    def __init__(self, database: Database) -> None:
        self._database: Database = database

    def get(self, key: str) -> Any:
        row = (
            self._database.connection()
            .execute("SELECT value FROM settings WHERE key = ?", (key,))
            .fetchone()
        )
        return json.loads(row["value"]) if row else None

    def set(self, key: str, value: Any) -> None:
        connection = self._database.connection()
        connection.execute(
            "INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, json.dumps(value)),
        )
        connection.commit()
