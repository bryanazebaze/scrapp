"""CentralImmo API — FastAPI application entry point.

Mounts all routers (annonces, search, neighborhoods, admin, health), configures
CORS for the Flutter frontend, and starts the APScheduler background scheduler
on startup. Seeds the two default admin accounts if the admin_users table is
empty (idempotent). A global exception handler guarantees no raw traceback or
internal payload ever reaches a client — all uncaught exceptions return a
generic French 500.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from core.database import SessionLocal
from core.scheduler import start_scheduler, shutdown_scheduler
from core.admin_auth import seed_admins_if_empty
from api.annonces import router as annonces_router
from api.search import router as search_router
from api.neighborhoods import router as neighborhoods_router
from api.admin import router as admin_router
from api.admin_auth import router as admin_auth_router
from api.auth import router as auth_router
from api.health import router as health_router
from api.profiles import router as profiles_router
from api.chat import router as chat_router
from api.payments import router as payments_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_scheduler()
    # Seed default admin accounts if the table is empty. Idempotent.
    try:
        db = SessionLocal()
        try:
            seed_admins_if_empty(db)
        finally:
            db.close()
    except Exception:
        logger.exception("admin seeding failed at startup")
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
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(annonces_router)
app.include_router(search_router)
app.include_router(neighborhoods_router)
app.include_router(admin_router)
app.include_router(admin_auth_router)
app.include_router(auth_router)
app.include_router(health_router)
app.include_router(profiles_router)
app.include_router(chat_router)
app.include_router(payments_router)


# Global exception handler — never leak raw tracebacks / payloads.
@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Erreur interne du serveur"},
    )


@app.get("/")
def bienvenue():
    return {
        "message": "Bienvenue sur CentralImmo API v3",
        "docs": "/docs",
        "health": "/health",
        "endpoints": [
            "/annonces", "/search", "/neighborhoods", "/profiles",
            "/admin", "/auth", "/health", "/chat", "/payments",
        ],
    }