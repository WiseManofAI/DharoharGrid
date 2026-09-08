import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

SIMILARITY_THRESHOLD = float(os.environ.get("SIMILARITY_THRESHOLD", "0.70"))
MATCH_COUNT = int(os.environ.get("MATCH_COUNT", "3"))
EMBEDDING_MODEL_NAME = os.environ.get("EMBEDDING_MODEL_NAME", "BAAI/bge-small-en-v1.5")
GROQ_MODEL_NAME = os.environ.get("GROQ_MODEL_NAME", "openai/gpt-oss-120b")

CORS_ALLOW_ORIGINS = os.environ.get("CORS_ALLOW_ORIGINS", "*").split(",")


def require_env():
    missing = [
        name
        for name, val in (
            ("SUPABASE_URL", SUPABASE_URL),
            ("SUPABASE_KEY", SUPABASE_KEY),
            ("GROQ_API_KEY", GROQ_API_KEY),
        )
        if not val
    ]
    if missing:
        raise RuntimeError(
            f"Missing required environment variable(s): {', '.join(missing)}. "
            "Copy .env.example to .env and fill them in."
        )
