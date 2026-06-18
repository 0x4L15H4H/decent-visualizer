import bcrypt
from fastapi import APIRouter, Cookie, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db import get_supabase
from app.dependencies import get_current_user
from app.models.auth import LoginRequest, SessionUser, SignupRequest, UserResponse
from app.storage.sessions import SessionStorage
from app.storage.settings import SettingsStorage
from app.storage.users import UserStorage

router = APIRouter(prefix="/auth", tags=["auth"])

SESSION_MAX_AGE = 30 * 24 * 60 * 60  # 30 days in seconds


def _set_session_cookie(response: JSONResponse, session_id: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key="session",
        value=session_id,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=settings.is_prod,
        path="/",
    )


@router.post("/signup", response_model=UserResponse)
def signup(data: SignupRequest):
    client = get_supabase()
    settings_storage = SettingsStorage(client)

    if not settings_storage.get("signups_enabled"):
        raise HTTPException(status_code=403, detail="Signups are currently disabled")

    user_storage = UserStorage(client)

    if user_storage.get_by_email(data.email) is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    password_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    user = user_storage.create(data.email, password_hash, data.display_name)

    session_storage = SessionStorage(client)
    session_row = session_storage.create(user.id)

    response = JSONResponse(content=user.model_dump(mode="json"), status_code=201)
    _set_session_cookie(response, session_row["id"])
    return response


@router.post("/login", response_model=UserResponse)
def login(data: LoginRequest):
    client = get_supabase()
    user_storage = UserStorage(client)
    row = user_storage.get_by_email(data.email)

    if row is None or not bcrypt.checkpw(data.password.encode(), row["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    session_storage = SessionStorage(client)
    session_row = session_storage.create(row["id"])

    user = UserResponse.model_validate(row)
    response = JSONResponse(content=user.model_dump(mode="json"))
    _set_session_cookie(response, session_row["id"])
    return response


@router.post("/logout")
def logout(session: str | None = Cookie(default=None)):
    if session is not None:
        client = get_supabase()
        SessionStorage(client).delete(session)
    response = JSONResponse(content={"ok": True})
    response.delete_cookie(key="session", path="/")
    return response


@router.get("/me", response_model=UserResponse)
def me(user: SessionUser = Depends(get_current_user)):
    client = get_supabase()
    user_storage = UserStorage(client)
    full_user = user_storage.get_by_id(user.id)
    if full_user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return full_user


@router.get("/signup-enabled")
def signup_enabled():
    client = get_supabase()
    settings_storage = SettingsStorage(client)
    enabled = settings_storage.get("signups_enabled")
    return {"enabled": bool(enabled)}
