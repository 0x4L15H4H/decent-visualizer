import base64
import binascii
import json
from typing import Any

from app.compression import compress_json, decompress_json
from app.db import Database
from app.models.shot import ShotSummary, ShotUpload, ShotUploadCreate, ShotUploadUpdate


class ShotStorage:
    def __init__(self, database: Database) -> None:
        self._database: Database = database

    def list(self) -> list[ShotSummary]:
        rows = self._database.connection().execute(
            "SELECT id,timestamp,duration,workflow FROM shots ORDER BY timestamp DESC"
        )
        return [
            ShotSummary.model_validate(
                {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "duration": row["duration"],
                    "coffee_name": json.loads(row["workflow"]).get("context", {}).get("coffeeName"),
                }
            )
            for row in rows
        ]

    def get(self, shot_id: str) -> ShotUpload | None:
        row = (
            self._database.connection()
            .execute("SELECT * FROM shots WHERE id = ?", (shot_id,))
            .fetchone()
        )
        return self._to_model(dict(row)) if row else None

    def create(self, shot_id: str, data: ShotUploadCreate) -> ShotUpload:
        values = data.model_dump(mode="json")
        connection = self._database.connection()
        connection.execute(
            """INSERT INTO shots(id,timestamp,duration,measurements,workflow,annotations,created_at)
            VALUES (?,?,?,?,?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now'))""",
            (
                shot_id,
                values["timestamp"],
                values["duration"],
                compress_json(values["measurements"]),
                json.dumps(values["workflow"]),
                json.dumps(values["annotations"]) if values["annotations"] is not None else None,
            ),
        )
        connection.commit()
        return self.get(shot_id)  # pyright: ignore[reportReturnType]

    def update(self, shot_id: str, data: ShotUploadUpdate) -> ShotUpload | None:
        values = data.model_dump(mode="json", exclude_unset=True)
        if not values:
            return self.get(shot_id)
        if "measurements" in values:
            values["measurements"] = compress_json(values["measurements"])
        for key in ("workflow", "annotations"):
            if key in values and values[key] is not None:
                values[key] = json.dumps(values[key])
        connection = self._database.connection()
        result = connection.execute(
            f"UPDATE shots SET {', '.join(f'{key} = ?' for key in values)} WHERE id = ?",
            (*values.values(), shot_id),
        )
        connection.commit()
        return self.get(shot_id) if result.rowcount else None

    def delete(self, shot_id: str) -> bool:
        connection = self._database.connection()
        result = connection.execute("DELETE FROM shots WHERE id = ?", (shot_id,))
        connection.commit()
        return result.rowcount > 0

    @staticmethod
    def _to_model(row: dict[str, Any]) -> ShotUpload:
        measurements = row["measurements"]
        row["measurements"] = decompress_json(
            decode_bytea(measurements) if isinstance(measurements, str) else bytes(measurements)
        )
        row["workflow"] = (
            json.loads(row["workflow"]) if isinstance(row["workflow"], str) else row["workflow"]
        )
        row["annotations"] = json.loads(row["annotations"]) if row["annotations"] else None
        return ShotUpload.model_validate(row)


def encode_bytea(data: bytes) -> str:
    return f"\\x{data.hex()}"


def decode_bytea(value: str) -> bytes:
    if value.startswith("\\x"):
        try:
            return bytes.fromhex(value[2:])
        except ValueError as error:
            raise ValueError("Invalid hexadecimal bytea value") from error
    try:
        return base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValueError("Invalid bytea value") from error
