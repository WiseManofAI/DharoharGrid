"""Lazily-constructed singletons, loaded once per process."""
from functools import lru_cache

from supabase import create_client, Client

from . import config


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    config.require_env()
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)


@lru_cache(maxsize=1)
def get_embedder():
    from sentence_transformers import SentenceTransformer

    print(f"[docent] loading embedding model {config.EMBEDDING_MODEL_NAME} ...")
    model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
    print("[docent] embedding model ready.")
    return model


@lru_cache(maxsize=1)
def get_groq():
    from groq import Groq

    config.require_env()
    return Groq(api_key=config.GROQ_API_KEY)
