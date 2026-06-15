import os
from functools import lru_cache
from typing import ClassVar, override

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class CloudflareConfig(BaseModel):
    pages_project: str


class Settings(BaseSettings):
    supabase_url: str
    supabase_service_key: str

    @property
    def cors_origins(self) -> list[str]:
        raise NotImplementedError


class ProdSettings(Settings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        json_file="config.json",
        extra="ignore",
    )
    domain: str
    cloudflare: CloudflareConfig

    @property
    @override
    def cors_origins(self) -> list[str]:
        return [
            f"https://{self.domain}",
            f"https://www.{self.domain}",
            f"https://{self.cloudflare.pages_project}.pages.dev",
        ]


class DevSettings(Settings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        json_file="../config/dev/backend.json",
        extra="ignore",
    )

    @property
    @override
    def cors_origins(self) -> list[str]:
        return []


@lru_cache
def get_settings() -> Settings:
    env = os.getenv("APP_ENV", "dev")
    if env == "prod":
        return ProdSettings()  # pyright: ignore[reportCallIssue]
    return DevSettings()  # pyright: ignore[reportCallIssue]
