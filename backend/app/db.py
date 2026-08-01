import sqlite3
import threading
from pathlib import Path

from app.config import get_settings
from app.schema import DEFAULT_PROCESSES, SCHEMA


class Database:
    def __init__(self, path: str) -> None:
        self._path: str = path
        self._local: threading.local = threading.local()

    def connection(self) -> sqlite3.Connection:
        connection = getattr(self._local, "connection", None)
        if connection is None:
            Path(self._path).parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(self._path)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(SCHEMA)
            connection.execute(
                "INSERT OR IGNORE INTO settings(key, value) VALUES ('signups_enabled', 'true')"
            )
            for name in DEFAULT_PROCESSES:
                connection.execute(
                    """INSERT OR IGNORE INTO canonical_entities
                    (id, kind, name, metadata, created_at, updated_at)
                    VALUES (lower(hex(randomblob(16))), 'process', ?, '{}',
                    strftime('%Y-%m-%dT%H:%M:%fZ','now'), strftime('%Y-%m-%dT%H:%M:%fZ','now'))""",
                    (name,),
                )
            connection.commit()
            self._local.connection = connection
        return connection


_database: Database | None = None


def get_database() -> Database:
    global _database
    if _database is None:
        _database = Database(get_settings().database_path)
    return _database
