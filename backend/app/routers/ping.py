from datetime import UTC, datetime

from fastapi import APIRouter

router = APIRouter()


@router.get("/ping")
def ping():
    return {
        "message": "pong",
        "timestamp": datetime.now(UTC).isoformat(),
    }
