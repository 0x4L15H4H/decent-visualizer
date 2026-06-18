from pydantic import BaseModel


class AppSettings(BaseModel):
    signups_enabled: bool = False


class AppSettingsUpdate(BaseModel):
    signups_enabled: bool | None = None
