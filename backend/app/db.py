from functools import lru_cache

from app.config import get_settings
from supabase import Client, create_client


@lru_cache
def get_supabase() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_key)
