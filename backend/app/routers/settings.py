from fastapi import APIRouter, Depends

from app.db import get_supabase
from app.dependencies import get_current_user
from app.models.settings import AppSettings, AppSettingsUpdate
from app.storage.settings import SettingsStorage

router = APIRouter(prefix="/settings", tags=["settings"], dependencies=[Depends(get_current_user)])


def _storage() -> SettingsStorage:
    return SettingsStorage(get_supabase())


@router.get("", response_model=AppSettings)
def get_settings(storage: SettingsStorage = Depends(_storage)):
    return AppSettings(
        signups_enabled=bool(storage.get("signups_enabled")),
    )


@router.patch("", response_model=AppSettings)
def update_settings(data: AppSettingsUpdate, storage: SettingsStorage = Depends(_storage)):
    if data.signups_enabled is not None:
        storage.set("signups_enabled", data.signups_enabled)
    return AppSettings(
        signups_enabled=bool(storage.get("signups_enabled")),
    )
