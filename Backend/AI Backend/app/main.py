from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .clients import get_embedder, get_groq, get_supabase
from .routers import docent


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm the embedding model / clients at startup rather than on the
    # first request, so the demo's first real question isn't the slow one.
    config.require_env()
    get_supabase()
    get_embedder()
    get_groq()
    print("[docent] startup complete.")
    yield


app = FastAPI(title="Cultural Docent API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(docent.router)


@app.get("/")
def root():
    return {"status": "Cultural Docent API is running."}
