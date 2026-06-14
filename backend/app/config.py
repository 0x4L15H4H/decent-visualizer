import json
import os
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path
from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings, ABC):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    supabase_url: str
    supabase_service_key: str

    @property
    @abstractmethod
    def cors_origins(self) -> list[str]: ...


class ProdSettings(Settings):
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
    @property
    def cors_origins(self) -> list[str]:
        return ["http://localhost:5173"]


def _find_config(name: str) -> dict:
    for base in [Path("config"), Path("../config")]:
        path = base / name
        if path.is_file():
            return json.loads(path.read_text())
    return {}


@lru_cache
def get_settings() -> Settings:
    env = os.getenv("APP_ENV", "dev")
    if env == "prod":
        return ProdSettings(**_find_config("prod.json"))  # pyright: ignore[reportCallIssue]
    return DevSettings()  # pyright: ignore[reportCallIssue]
