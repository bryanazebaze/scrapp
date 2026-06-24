"""Health check endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.database import get_db
from core.config import settings
from core.schemas import HealthSchema

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthSchema)
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "error"
    scheduler_running = False
    try:
        from core.scheduler import get_scheduler
        scheduler_running = get_scheduler().running
    except Exception:
        pass
    return HealthSchema(
        status="ok" if db_status == "connected" else "degraded",
        version="3.0.0",
        database=db_status,
        scheduler_running=scheduler_running,
    )