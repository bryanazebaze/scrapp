"""CentralImmo API — FastAPI application entry point.

Mounts all routers (annonces, search, neighborhoods, admin, health), configures
CORS for the Flutter frontend, and starts the APScheduler background scheduler
on startup.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.scheduler import start_scheduler, shutdown_scheduler
from api.annonces import router as annonces_router
from api.search import router as search_router
from api.neighborhoods import router as neighborhoods_router
from api.admin import router as admin_router
from api.health import router as health_router
from api.profiles import router as profiles_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_scheduler()
    yield
    # Shutdown
    shutdown_scheduler()


app = FastAPI(
    title="CentralImmo API",
    description="Plateforme d'agrégation et d'intelligence immobilière du Cameroun",
    version="3.0.0",
    lifespan=lifespan,
)

# CORS — allow the Flutter app (web, desktop, mobile) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(annonces_router)
app.include_router(search_router)
app.include_router(neighborhoods_router)
app.include_router(admin_router)
app.include_router(health_router)
app.include_router(profiles_router)


@app.get("/")
def bienvenue():
    return {
        "message": "Bienvenue sur CentralImmo API v3",
        "docs": "/docs",
        "health": "/health",
        "endpoints": [
            "/annonces", "/search", "/neighborhoods", "/profiles",
            "/admin", "/health",
        ],
    }