import os
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings, ABC):
    supabase_url: str
    supabase_service_key: str

    @property
    @abstractmethod
    def cors_origins(self) -> list[str]: ...


class ProdSettings(Settings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        json_file="config.json",
        extra="ignore",
    )
    domain: str
    cloudflare_pages_project: str

    @property
    def cors_origins(self) -> list[str]:
        return [
            f"https://{self.domain}",
            f"https://www.{self.domain}",
            f"https://{self.cloudflare_pages_project}.pages.dev",
        ]


class DevSettings(Settings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        json_file="../config/dev/backend.json",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return []


@lru_cache
def get_settings() -> Settings:
    env = os.getenv("APP_ENV", "dev")
    if env == "prod":
        return ProdSettings()  # pyright: ignore[reportCallIssue]
    return DevSettings()  # pyright: ignore[reportCallIssue]
