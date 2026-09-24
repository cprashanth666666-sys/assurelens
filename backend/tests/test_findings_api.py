"""The findings and roadmap API. [Day 8]

Pins the HTTP surface the findings register, the overview heatmap and the
roadmap screen consume.

The write endpoints here (`POST /runs` semantics reused via `run_suites`,
and `PATCH /findings/{ref}`) commit for real in production -- `get_db`'s
`finally: db.close()` would otherwise silently discard every change when
the request ends, which is a production bug, not a test convenience, so
the endpoints keep their own `db.commit()` exactly like `runs.py` does.

That means a naive shared-session override would make every commit in this
file permanent in the session-scoped `seeded_estate` database, corrupting
whatever test file happens to run afterward. Instead this module opens its
own connection from the same engine, wraps it in an outer transaction plus
a SAVEPOINT (`join_transaction_mode="create_savepoint"`), and points both
the direct `run_suites` calls and the API (via a `get_db` override) at
sessions bound to that one connection. A `COMMIT` issued through the API
only closes the savepoint; the real, outer transaction rolls back
everything in teardown, so nothing written here outlives the test.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app import suites as _suites  # noqa: F401  registers procedures
from app.db import get_db
from app.engine.collectors import default_broker
from app.engine.runner import run_suites
from app.main import app
from app.models.control import Engagement

pytestmark = pytest.mark.usefixtures("seeded_estate")


@pytest.fixture
def db(seeded_estate: Session) -> Iterator[Session]:
    """A session pinned to its own connection and SAVEPOINT, so a commit
    made through the API cannot escape this one test."""
    engine = seeded_estate.get_bind()
    connection = engine.connect()
    outer = connection.begin()
    factory = sessionmaker(
        bind=connection, expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    session = factory()
    try:
        yield session
    finally:
        session.close()
        outer.rollback()
        connection.close()


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db
    try:
        yield TestClient(app)
    finally:
        del app.dependency_overrides[get_db]


@pytest.fixture
def engagement_id(db: Session) -> int:
    engagement = db.scalar(select(Engagement).order_by(Engagement.id).limit(1))
    assert engagement is not None
    return engagement.id


@pytest.fixture
def ran(db: Session, engagement_id: int) -> Session:
    """Findings raised via the real engine, on the same connection the API
    reads from."""
    run_suites(
        db, engagement_id,
        ["consent", "pii_retention", "third_party", "ai_assurance"],
        seed=42, broker=default_broker(), engine_version="test",
    )
    db.commit()
    return db


def test_listing_findings_returns_what_the_run_raised(
    client: TestClient, ran: Session, engagement_id: int,
) -> None:
    response = client.get(f"/api/engagements/{engagement_id}/findings")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 8
    assert {f["control_ref"] for f in body} >= {"DPDP-TP-01", "DPDP-13-02"}
    for f in body:
        assert f["severity"] in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
        assert f["risk_score"] == f["likelihood"] * f["impact"]


def test_listing_an_unknown_engagement_404s(client: TestClient) -> None:
    response = client.get("/api/engagements/999999/findings")
    assert response.status_code == 404


def test_the_heatmap_filter_returns_exactly_that_cell(
    client: TestClient, ran: Session, engagement_id: int,
) -> None:
    all_findings = client.get(f"/api/engagements/{engagement_id}/findings").json()
    target = all_findings[0]
    response = client.get(
        f"/api/engagements/{engagement_id}/findings",
        params={"likelihood": target["likelihood"], "impact": target["impact"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 1
    assert all(
        f["likelihood"] == target["likelihood"] and f["impact"] == target["impact"]
        for f in body
    )


def test_the_status_filter_uses_the_status_query_param_not_status_(
    client: TestClient, ran: Session, engagement_id: int,
) -> None:
    """Regression: the handler's parameter is named status_ (status is a
    stdlib/fastapi name), but the wire format must still be ?status=."""
    response = client.get(
        f"/api/engagements/{engagement_id}/findings", params={"status": "OPEN"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 8

    response = client.get(
        f"/api/engagements/{engagement_id}/findings", params={"status": "CLOSED"},
    )
    assert response.json() == []


def test_getting_one_finding_includes_its_history(
    client: TestClient, ran: Session, engagement_id: int,
) -> None:
    ref = client.get(f"/api/engagements/{engagement_id}/findings").json()[0]["ref"]
    response = client.get(f"/api/findings/{ref}")
    assert response.status_code == 200
    body = response.json()
    assert body["ref"] == ref
    assert isinstance(body["history"], list)


def test_getting_an_unknown_finding_404s(client: TestClient) -> None:
    assert client.get("/api/findings/F-999").status_code == 404


def test_patching_a_finding_updates_it_and_logs_history(
    client: TestClient, ran: Session, engagement_id: int,
) -> None:
    ref = client.get(f"/api/engagements/{engagement_id}/findings").json()[0]["ref"]

    response = client.patch(
        f"/api/findings/{ref}",
        json={"owner": "Vendor Management, Meridian India", "status": "IN_REMEDIATION"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["owner"] == "Vendor Management, Meridian India"
    assert body["status"] == "IN_REMEDIATION"
    fields_changed = {h["field"] for h in body["history"]}
    assert {"owner", "status"} <= fields_changed


def test_patching_likelihood_recomputes_severity(
    client: TestClient, ran: Session, engagement_id: int,
) -> None:
    ref = client.get(f"/api/engagements/{engagement_id}/findings").json()[0]["ref"]
    before = client.get(f"/api/findings/{ref}").json()

    response = client.patch(f"/api/findings/{ref}", json={"likelihood": 1, "impact": 1})
    assert response.status_code == 200
    body = response.json()
    assert body["risk_score"] == 1
    assert body["severity"] == "LOW"
    if before["severity"] != "LOW":
        assert any(h["field"] == "severity" for h in body["history"])


def test_patching_an_invalid_status_is_rejected(
    client: TestClient, ran: Session, engagement_id: int,
) -> None:
    ref = client.get(f"/api/engagements/{engagement_id}/findings").json()[0]["ref"]
    response = client.patch(f"/api/findings/{ref}", json={"status": "WONTFIX"})
    assert response.status_code == 422


def test_patching_an_unknown_finding_404s(client: TestClient) -> None:
    response = client.patch("/api/findings/F-999", json={"owner": "x"})
    assert response.status_code == 404


def test_the_roadmap_is_ordered_by_impact_over_effort_highest_first(
    client: TestClient, ran: Session, engagement_id: int,
) -> None:
    response = client.get(f"/api/engagements/{engagement_id}/roadmap")
    assert response.status_code == 200
    body = response.json()
    assert "÷" in body["ordering_rule"] or "impact" in body["ordering_rule"].lower()

    priorities = [item["priority"] for item in body["items"]]
    assert priorities == sorted(priorities, reverse=True)
    assert [item["sequence"] for item in body["items"]] == list(
        range(1, len(body["items"]) + 1)
    )


def test_the_roadmap_excludes_closed_findings(
    client: TestClient, ran: Session, engagement_id: int,
) -> None:
    ref = client.get(f"/api/engagements/{engagement_id}/findings").json()[0]["ref"]
    client.patch(f"/api/findings/{ref}", json={"status": "CLOSED"})

    body = client.get(f"/api/engagements/{engagement_id}/roadmap").json()
    assert ref not in {item["ref"] for item in body["items"]}


def test_the_roadmap_priority_matches_the_printed_impact_and_effort(
    client: TestClient, ran: Session, engagement_id: int,
) -> None:
    body = client.get(f"/api/engagements/{engagement_id}/roadmap").json()
    for item in body["items"]:
        assert item["priority"] == pytest.approx(item["impact"] / item["effort_days"], abs=1e-3)
