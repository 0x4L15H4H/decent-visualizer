from functools import lru_cache
from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=("../config.env", "config.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )
    supabase_url: str
    supabase_service_key: str
    domain: str
    cloudflare_pages_project: str

    @property
    def cors_origins(self) -> list[str]:
        # Mirror the infra CORS allow-list. Credentialed CORS forbids a
        # wildcard, so the origins are listed explicitly.
        return [
            f"https://{self.domain}",
            f"https://www.{self.domain}",
            f"https://{self.cloudflare_pages_project}.pages.dev",
        ]


@lru_cache
def get_settings() -> Settings:
    # basedpyright sees the properties as required __init__ args (no defaults),
    # but pydantic-settings fulfills them from env vars at runtime.
    # No pyright plugin exists yet to model this.
    return Settings()  # pyright: ignore[reportCallIssue]
