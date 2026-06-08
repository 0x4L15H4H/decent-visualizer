from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
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
    return Settings()
