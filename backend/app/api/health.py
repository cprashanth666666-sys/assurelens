"""Health endpoint.

The frontend calls this on first paint to wake a sleeping free-tier backend
while rendering cached content, so a cold link never shows only a spinner.
[TRD 1.4]
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    engine_version: str
    database: str


@router.get("/health", response_model=HealthResponse)
def health(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    try:
        db.execute(text("SELECT 1"))
        database = "up"
    except Exception:  # noqa: BLE001 — health must report, not raise.
        database = "down"

    return HealthResponse(
        status="ok" if database == "up" else "degraded",
        engine_version=settings.engine_version,
        database=database,
    )
