from functools import lru_cache

from supabase import create_client, Client

from . import config


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    config.require_env()
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
