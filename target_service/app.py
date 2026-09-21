"""Meridian customer API — DELIBERATELY VULNERABLE TARGET SERVICE.

This is not AssureLens. It is the *system under test*: a stand-in for a client
application, carrying intentional defects that the access-control suite probes
over HTTP. See README.md before touching anything here.

Day 1 ships the skeleton and the labelling. Day 3 plants the defects.
"""

import logging
import os

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))

WARNING = (
    "This service is deliberately vulnerable and exists only as a test target "
    "for AssureLens. It holds synthetic data, has no database credentials, and "
    "must never be deployed against a real system."
)

app = FastAPI(
    title="Meridian Customer API (deliberately vulnerable test target)",
    description=WARNING,
    version="0.1.0",
)


class Root(BaseModel):
    service: str
    warning: str
    synthetic_data_only: bool


@app.get("/", response_model=Root)
def root() -> Root:
    """Unmistakable labelling is a build requirement, not a nicety. [TRD 9]"""
    return Root(
        service="Meridian Customer API — TEST TARGET",
        warning=WARNING,
        synthetic_data_only=True,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
