import json
import zlib
from typing import Any


def compress_json(data: Any) -> bytes:
    """Serialize JSON-compatible data and compress it as a zlib stream."""
    raw = json.dumps(data, separators=(",", ":")).encode("utf-8")
    return zlib.compress(raw)


def decompress_json(data: bytes) -> Any:
    """Decompress a zlib stream and deserialize its JSON payload."""
    raw = zlib.decompress(data)
    return json.loads(raw.decode("utf-8"))
