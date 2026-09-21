"""Health endpoint.

The frontend calls this on first paint to wake a sleeping free-tier backend
while rendering cached content, so a cold link never shows only a spinner.
[TRD 1.4]

It deliberately does NOT take `get_db` as a dependency. A dependency that
raises during resolution produces an opaque 500, which is precisely what this
endpoint exists to avoid — it must always answer, and name what is wrong.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text

from app.config import Settings, get_settings
from app.db import DatabaseConfigurationError, get_engine

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    engine_version: str
    database: str
    detail: str | None = None


def _check_database() -> tuple[str, str | None]:
    """Probe the database, distinguishing misconfiguration from unreachability.

    The two look identical from the outside and have opposite remedies: a
    sleeping instance resolves itself in thirty seconds, a bad DATABASE_URL
    never does. Reporting them as one state leaves an operator waiting for a
    cold start that will not arrive.
    """
    try:
        engine = get_engine()
    except DatabaseConfigurationError as exc:
        return "misconfigured", str(exc)

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — health reports, it never raises.
        return "down", type(exc).__name__

    return "up", None


@router.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    database, detail = _check_database()

    return HealthResponse(
        status="ok" if database == "up" else "degraded",
        engine_version=settings.engine_version,
        database=database,
        detail=detail,
    )
