from functools import lru_cache
from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
    supabase_url: str
    supabase_service_key: str
    # Comma-separated list of allowed origins. Required — credentialed CORS
    # cannot use a wildcard, so an explicit list must always be provided.
    # Example: "https://example.com,https://www.example.com"
    cors_origins: str


@lru_cache
def get_settings() -> Settings:
    # basedpyright sees the properties as required __init__ args (no defaults),
    # but pydantic-settings fulfills them from env vars at runtime.
    # No pyright plugin exists yet to model this.
    return Settings()  # pyright: ignore[reportCallIssue]
