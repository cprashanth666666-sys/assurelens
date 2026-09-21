"""Day 1 smoke tests: the app boots, and health reports rather than raises."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200_even_without_a_database() -> None:
    """Health must always answer.

    A health endpoint that 500s when the database is asleep is useless
    precisely when it is needed — the frontend calls it to wake a sleeping
    free-tier backend. [TRD 1.4]
    """
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert body["database"] in {"up", "down"}
    assert body["engine_version"]


def test_openapi_documents_the_synthetic_data_constraint() -> None:
    """The API description states that it operates on synthetic data only.

    This is a standing disclosure, not decoration. [PRD 9]
    """
    schema = client.get("/openapi.json").json()

    assert "synthetic" in schema["info"]["description"].lower()
