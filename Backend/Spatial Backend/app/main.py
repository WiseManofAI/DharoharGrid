from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .routers import spatial

app = FastAPI(title="DharoharGrid Spatial API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(spatial.router)


@app.get("/")
def root():
    return {"status": "DharoharGrid Spatial API is running."}
