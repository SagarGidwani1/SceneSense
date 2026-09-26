import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import routes_brands, routes_health, routes_videos
from app.config import STORAGE_PATH

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                    handlers=[logging.StreamHandler(sys.stdout)])

app = FastAPI(title="SceneSense API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

for r in (routes_health, routes_videos, routes_brands):
    app.include_router(r.router, prefix="/api")

for sub in ("ads", "uploads", "scenes"):
    app.mount(f"/public/{sub}", StaticFiles(directory=str(STORAGE_PATH / sub)), name=sub)


@app.get("/")
def root():
    return {"service": "SceneSense API", "docs": "/docs", "health": "/api/health"}
