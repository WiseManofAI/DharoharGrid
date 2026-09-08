"""Lazily-constructed singletons: Supabase client, embedding model, LLM client.

Lazy so importing this module (e.g. from the FastAPI app, which only needs
Supabase to serve cached reads) never pays the cost of loading the
sentence-transformers model unless something actually calls get_embedder().
"""
from __future__ import annotations

import json
import time
from functools import lru_cache
from typing import Any

import requests
from supabase import create_client, Client

from . import config


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    config.require_supabase()
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)


@lru_cache(maxsize=1)
def get_embedder():
    """Loads the sentence-transformers model once per process."""
    from sentence_transformers import SentenceTransformer

    print(f"[obsidian] loading embedding model {config.EMBEDDING_MODEL_NAME} ...")
    model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
    print("[obsidian] embedding model ready.")
    return model


class LLMError(RuntimeError):
    pass


class LLMClient:
    """Thin wrapper around any OpenAI-compatible /chat/completions endpoint.

    Works unmodified against Groq (default), OpenAI, Together, Fireworks, a
    local Ollama/vLLM server — anything that speaks the same wire format.
    Swap provider by changing LLM_BASE_URL / LLM_API_KEY / LLM_MODEL in .env.
    """

    def __init__(self):
        config.require_llm()
        self.base_url = config.LLM_BASE_URL.rstrip("/")
        self.api_key = config.LLM_API_KEY
        self.model = config.LLM_MODEL

    def chat_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> Any:
        """Sends a chat completion request and parses the reply as JSON.

        Retries with exponential backoff on rate limits (429) and transient
        5xx errors. Raises LLMError if the model's reply isn't valid JSON
        after all retries — callers should treat that as "skip this batch",
        never as license to fabricate a result.
        """
        payload = {
            "model": self.model,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_err: Exception | None = None
        for attempt in range(config.LLM_MAX_RETRIES):
            try:
                resp = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=config.LLM_TIMEOUT_SECONDS,
                )
                if resp.status_code == 429 or resp.status_code >= 500:
                    wait = min(2 ** attempt, 20)
                    print(f"[obsidian] LLM {resp.status_code}, retrying in {wait}s...")
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
                return json.loads(content)
            except (requests.RequestException, KeyError, json.JSONDecodeError) as e:
                last_err = e
                wait = min(2 ** attempt, 20)
                time.sleep(wait)

        raise LLMError(f"LLM call failed after {config.LLM_MAX_RETRIES} attempts: {last_err}")
