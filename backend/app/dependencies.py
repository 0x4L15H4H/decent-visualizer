from datetime import UTC, datetime

from fastapi import Cookie, HTTPException

from app.db import get_supabase
from app.models.auth import SessionUser
from app.storage.sessions import SessionStorage
from app.storage.users import UserStorage


def get_current_user(session: str | None = Cookie(default=None)) -> SessionUser:
    if session is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    client = get_supabase()
    session_storage = SessionStorage(client)
    row = session_storage.get(session)

    if row is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if datetime.fromisoformat(row["expires_at"]) < datetime.now(UTC):
        session_storage.delete_expired(session)
        raise HTTPException(status_code=401, detail="Session expired")

    user_storage = UserStorage(client)
    user = user_storage.get_by_id(row["user_id"])

    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return SessionUser(id=user.id, email=user.email, display_name=user.display_name)
