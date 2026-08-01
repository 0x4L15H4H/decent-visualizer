"""One-time, idempotent import of the production Supabase data into SQLite."""

import json
import sys
from datetime import UTC, datetime
from typing import cast
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.config import get_settings
from app.db import get_database
from app.storage.shots import decode_bytea

TABLES = ("users", "settings", "canonical_entities", "entity_aliases", "beans", "shots", "sessions")


def fetch_table(base_url: str, key: str, table: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for offset in range(0, 1_000_000, 1000):
        query = urlencode({"select": "*", "offset": offset, "limit": 1000})
        request = Request(
            f"{base_url.rstrip('/')}/rest/v1/{table}?{query}",
            headers={"apikey": key, "Authorization": f"Bearer {key}"},
        )
        with urlopen(request, timeout=30) as response:
            page = cast(object, json.load(response))
        if not isinstance(page, list):
            raise RuntimeError(f"Unexpected response while importing {table}")
        typed_page = cast(list[dict[str, object]], page)
        rows.extend(typed_page)
        if len(typed_page) < 1000:
            return rows
    raise RuntimeError(f"Too many rows while importing {table}")


def import_data() -> None:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_key:
        raise RuntimeError(
            "supabase_url and supabase_service_key are required for the one-time import"
        )
    database = get_database()
    connection = database.connection()
    if connection.execute("SELECT 1 FROM settings WHERE key = 'supabase_imported_at'").fetchone():
        print("SQLite already contains the Supabase import; nothing to do.")
        return

    source = {
        table: fetch_table(settings.supabase_url, settings.supabase_service_key, table)
        for table in TABLES
    }
    with connection:
        # The freshly initialized database has seeded process entities. Source IDs must be preserved.
        for table in reversed(TABLES):
            connection.execute(f"DELETE FROM {table}")
        for row in source["users"]:
            connection.execute(
                "INSERT INTO users VALUES (?,?,?,?,?)",
                tuple(
                    row[key]
                    for key in ("id", "email", "password_hash", "display_name", "created_at")
                ),
            )
        for row in source["settings"]:
            connection.execute(
                "INSERT INTO settings VALUES (?,?)", (row["key"], json.dumps(row["value"]))
            )
        for row in source["canonical_entities"]:
            connection.execute(
                "INSERT INTO canonical_entities VALUES (?,?,?,?,?,?,?)",
                (
                    row["id"],
                    row["kind"],
                    row["name"],
                    row.get("country_code"),
                    json.dumps(row.get("metadata") or {}),
                    row["created_at"],
                    row["updated_at"],
                ),
            )
        for row in source["entity_aliases"]:
            connection.execute(
                "INSERT INTO entity_aliases VALUES (?,?,?,?,?)",
                tuple(row[key] for key in ("id", "entity_id", "alias", "source", "created_at")),
            )
        for row in source["beans"]:
            connection.execute(
                "INSERT INTO beans VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                tuple(
                    row.get(key)
                    for key in (
                        "id",
                        "name",
                        "roaster_id",
                        "producer_id",
                        "farm_id",
                        "country_code",
                        "variety_id",
                        "process_id",
                        "roast_level",
                        "roast_date",
                        "notes",
                        "created_at",
                    )
                ),
            )
        for row in source["shots"]:
            measurements = row["measurements"]
            connection.execute(
                "INSERT INTO shots VALUES (?,?,?,?,?,?,?)",
                (
                    row["id"],
                    row["timestamp"],
                    row["duration"],
                    decode_bytea(measurements) if isinstance(measurements, str) else measurements,
                    json.dumps(row["workflow"]),
                    json.dumps(row["annotations"]) if row.get("annotations") is not None else None,
                    row["created_at"],
                ),
            )
        for row in source["sessions"]:
            connection.execute(
                "INSERT INTO sessions VALUES (?,?,?,?)",
                tuple(row[key] for key in ("id", "user_id", "created_at", "expires_at")),
            )
        connection.execute(
            "INSERT INTO settings VALUES (?,?)",
            ("supabase_imported_at", json.dumps(datetime.now(UTC).isoformat())),
        )
    print("Imported Supabase data into SQLite.")


if __name__ == "__main__":
    try:
        import_data()
    except Exception as error:
        print(f"SQLite import failed: {error}", file=sys.stderr)
        raise
