import json
from typing import cast

import pytest
from postgrest.types import JSON

from app.compression import compress_json, decompress_json
from app.storage.shots import ShotStorage, decode_bytea, encode_bytea

MEASUREMENTS = [
    {
        "elapsed": 0.1,
        "machine": {
            "timestamp": "2026-06-27T12:00:00Z",
            "state": {"state": "espresso", "substate": "pouring"},
            "flow": 2.0,
            "pressure": 8.5,
            "targetFlow": 2.2,
            "targetPressure": 9.0,
            "mixTemperature": 92.0,
            "groupTemperature": 91.5,
            "targetMixTemperature": 93.0,
            "targetGroupTemperature": 92.0,
            "profileFrame": 1,
        },
    }
]


def shot_row() -> dict[str, object]:
    return {
        "id": "shot-1",
        "timestamp": "2026-06-27T12:00:00Z",
        "duration": 30.0,
        "measurements": MEASUREMENTS,
        "workflow": {"id": "workflow-1", "name": "Test", "profile": {}},
        "annotations": None,
        "created_at": "2026-06-27T12:01:00Z",
    }


def test_compress_json_round_trips_nested_data() -> None:
    data = {
        "name": "Café",
        "measurements": [
            {"elapsed": 0.1, "pressure": 2.5},
            {"elapsed": 0.2, "pressure": 3.0},
        ],
    }

    compressed = compress_json(data)

    assert decompress_json(compressed) == data
    assert len(compressed) < len(json.dumps(data).encode("utf-8"))


def test_bytea_hex_round_trip() -> None:
    compressed = compress_json([{"elapsed": 0.1}])

    encoded = encode_bytea(compressed)

    assert encoded.startswith("\\x")
    assert decode_bytea(encoded) == compressed


def test_bytea_decoder_accepts_base64_for_compatibility() -> None:
    assert decode_bytea("eJyrVkrLz1eyUkpKLFKqBQAdegQ0") == (
        b"x\x9c\xabVJ\xcb\xcfW\xb2RJJ,R\xaa\x05\x00\x1dz\x044"
    )


def test_bytea_decoder_rejects_invalid_data() -> None:
    with pytest.raises(ValueError, match="Invalid bytea"):
        decode_bytea("not bytea!")


def test_shot_storage_reads_compressed_measurements() -> None:
    row = shot_row()
    row["measurements"] = encode_bytea(compress_json(MEASUREMENTS))

    model = ShotStorage._to_model(  # pyright: ignore[reportPrivateUsage]
        cast(JSON, row)
    )

    assert model.measurements[0].machine.pressure == 8.5
