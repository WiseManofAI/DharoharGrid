from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .routers import graph, submissions

app = FastAPI(
    title="DharoharGrid Obsidian/Synapse API",
    description=(
        "Read-only API over the precomputed discovery graph (nodes, "
        "supercluster/subcluster taxonomy, AI-formed synapse edges). Build "
        "or refresh the graph with `python -m app.pipeline.build_graph`."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(graph.router)
app.include_router(submissions.router)


@app.get("/")
def root():
    return {"status": "DharoharGrid Obsidian/Synapse API is running."}
