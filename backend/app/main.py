"""AssureLens API.

A DPDP + AI controls assurance workbench. See docs/TRD.md for architecture.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Imported for its side effect: registering every suite procedure and
# evidence source. Without it the registry is empty and every executable
# control gates on missing evidence.
#
# `from app import suites`, never `import app.suites`: the latter binds the
# name `app` in this module, shadowing the FastAPI instance defined below --
# so `app.include_router` would look for a router method on the package.
from app import suites as _suites  # noqa: F401
from app.api import controls, health, runs
from app.config import get_settings

settings = get_settings()
logging.basicConfig(level=settings.log_level)

app = FastAPI(
    title="AssureLens API",
    description=(
        "Turns the DPDP Act and Rules 2025 into executable controls, runs real "
        "tests, and gates every verdict on evidence sufficiency. "
        "Operates on synthetic data only."
    ),
    version=settings.engine_version,
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(controls.router, prefix="/api", tags=["controls"])
app.include_router(runs.router, prefix="/api", tags=["runs"])
