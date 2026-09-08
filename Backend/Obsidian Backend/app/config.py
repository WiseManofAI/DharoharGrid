"""Central config for the Obsidian (synapse/discovery-graph) backend.

Every setting is overridable via environment variables (.env). Defaults are
chosen so the pipeline runs safely out of the box, but nothing here is
hardcoded elsewhere in the codebase — this is the single place to tune it.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Supabase
# ---------------------------------------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# ---------------------------------------------------------------------------
# LLM — pluggable, OpenAI-compatible chat-completions endpoint.
# Defaults to Groq, but pointing LLM_BASE_URL/LLM_API_KEY/LLM_MODEL at any
# other OpenAI-compatible provider (OpenAI, Together, Fireworks, a local
# Ollama server, etc.) works without touching code.
# ---------------------------------------------------------------------------
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.groq.com/openai/v1")
LLM_API_KEY = os.environ.get("LLM_API_KEY") or os.environ.get("GROQ_API_KEY")
LLM_MODEL = os.environ.get("LLM_MODEL", "openai/gpt-oss-120b")
LLM_TIMEOUT_SECONDS = float(os.environ.get("LLM_TIMEOUT_SECONDS", "60"))
LLM_MAX_RETRIES = int(os.environ.get("LLM_MAX_RETRIES", "4"))

# ---------------------------------------------------------------------------
# Embedding model (shared with the AI Backend docent — same model name so
# query embeddings and node embeddings live in the same vector space)
# ---------------------------------------------------------------------------
EMBEDDING_MODEL_NAME = os.environ.get("EMBEDDING_MODEL_NAME", "BAAI/bge-small-en-v1.5")

# ---------------------------------------------------------------------------
# Pipeline tuning
# ---------------------------------------------------------------------------
SYNAPSE_TOP_K = int(os.environ.get("SYNAPSE_TOP_K", "6"))
SYNAPSE_MIN_COSINE = float(os.environ.get("SYNAPSE_MIN_COSINE", "0.35"))
SYNAPSE_BATCH_SIZE = int(os.environ.get("SYNAPSE_BATCH_SIZE", "5"))
DEDUPE_COSINE_THRESHOLD = float(os.environ.get("DEDUPE_COSINE_THRESHOLD", "0.93"))
ENRICH_BATCH_SIZE = int(os.environ.get("ENRICH_BATCH_SIZE", "1"))

# Source dataset the seed step loads from (the same file map.html/Discover's
# client-side fallback are built from, so backend and frontend agree).
REPO_ROOT = Path(__file__).resolve().parents[3]
RAW_DATASET_PATH = REPO_ROOT / "map_rough" / "SIH" / "rajasthan_master.json"

# ---------------------------------------------------------------------------
# API-layer cache (the graph only changes when the pipeline reruns, so the
# read endpoints cache their response instead of re-querying Supabase per
# request — this is what keeps /api/v1/graph/full fast under load).
# ---------------------------------------------------------------------------
GRAPH_CACHE_TTL_SECONDS = int(os.environ.get("GRAPH_CACHE_TTL_SECONDS", "300"))

CORS_ALLOW_ORIGINS = os.environ.get("CORS_ALLOW_ORIGINS", "*").split(",")


def require_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError(
            "SUPABASE_URL / SUPABASE_KEY are not set. Copy .env.example to "
            ".env and fill them in."
        )


def require_llm():
    if not LLM_API_KEY:
        raise RuntimeError(
            "LLM_API_KEY (or GROQ_API_KEY) is not set. Copy .env.example to "
            ".env and fill it in."
        )
