"""Health must always answer, and must name what is wrong.

A health endpoint that 500s when the database is asleep is useless precisely
when it is needed — the frontend calls it to wake a sleeping free-tier
backend. [TRD 1.4]
"""

import pytest
from fastapi.testclient import TestClient

from app import db as db_module
from app.config import get_settings
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_lazy_state() -> None:
    """Clear the cached engine and settings between tests.

    Both are memoised deliberately, so a test that changes the environment
    must reset them or it leaks into the next one.
    """
    db_module._engine = None
    db_module._session_factory = None
    get_settings.cache_clear()


def test_health_answers_without_a_database() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert body["database"] in {"up", "down", "misconfigured"}
    assert body["engine_version"]


def test_health_survives_an_unparseable_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A bad DATABASE_URL must not take the application down.

    Building the engine at import time made this impossible: SQLAlchemy raised
    ArgumentError before FastAPI was constructed, so uvicorn never started and
    the operator saw a generic boot failure with no diagnostic.
    """
    monkeypatch.setenv("DATABASE_URL", "not-a-valid-url")
    get_settings.cache_clear()
    db_module._engine = None
    db_module._session_factory = None

    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["database"] == "misconfigured"
    assert body["status"] == "degraded"
    # The remedy differs from a cold start, so the response has to say which.
    assert body["detail"]


def test_misconfigured_is_distinct_from_down(monkeypatch: pytest.MonkeyPatch) -> None:
    """The two states look identical outside and have opposite remedies.

    A sleeping instance resolves itself in thirty seconds; a bad URL never
    does. Collapsing them leaves an operator waiting for a cold start that
    will not arrive.
    """
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://nobody:nobody@127.0.0.1:59999/nothing",
    )
    get_settings.cache_clear()
    db_module._engine = None
    db_module._session_factory = None

    body = client.get("/api/health").json()

    assert body["database"] == "down"  # reachable config, unreachable server


def test_openapi_documents_the_synthetic_data_constraint() -> None:
    """The API states that it operates on synthetic data only. [PRD 9]"""
    schema = client.get("/openapi.json").json()

    assert "synthetic" in schema["info"]["description"].lower()
