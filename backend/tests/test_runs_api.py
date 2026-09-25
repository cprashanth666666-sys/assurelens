"""The run API.

The engine is proven by test_runner.py, but it is only reachable in-process.
These tests pin the HTTP surface the run console consumes: without it the
engine exists and nothing can start it.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.main import app
from app.models.control import Engagement

pytestmark = pytest.mark.usefixtures("seeded_db")

client = TestClient(app)


@pytest.fixture
def engagement_id(seeded_db: Session) -> int:
    engagement = seeded_db.scalar(select(Engagement).order_by(Engagement.id).limit(1))
    assert engagement is not None
    return engagement.id


def test_starting_a_run_returns_its_identity(engagement_id: int) -> None:
    response = client.post(
        f"/api/engagements/{engagement_id}/runs",
        json={"suite_ids": ["pii_retention"], "seed": 42},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["seed"] == 42
    assert body["status"] in {"RUNNING", "COMPLETE"}
    assert body["id"] > 0


def test_the_seed_defaults_so_a_run_is_always_reproducible(
    engagement_id: int,
) -> None:
    """A run with no recorded seed cannot be regenerated, which makes its
    results an assertion rather than a finding."""
    response = client.post(
        f"/api/engagements/{engagement_id}/runs", json={"suite_ids": ["consent"]}
    )

    assert response.status_code == 201
    assert response.json()["seed"] is not None


def test_a_run_can_be_read_back_with_its_results(engagement_id: int) -> None:
    created = client.post(
        f"/api/engagements/{engagement_id}/runs",
        json={"suite_ids": ["pii_retention"], "seed": 7},
    ).json()

    response = client.get(f"/api/runs/{created['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["seed"] == 7
    assert isinstance(body["results"], list)


def test_a_scoped_out_control_appears_in_the_results(engagement_id: int) -> None:
    """DPDP-08-04 does not bind a BFSI GCC. It must be reported as
    NOT_APPLICABLE with its reason, not silently absent -- a control missing
    from a workpaper is the gap nobody notices."""
    created = client.post(
        f"/api/engagements/{engagement_id}/runs",
        json={"suite_ids": ["pii_retention"], "seed": 1},
    ).json()

    results = client.get(f"/api/runs/{created['id']}").json()["results"]
    scoped_out = [r for r in results if r["control_ref"] == "DPDP-08-04"]

    assert scoped_out, "the excluded control must still be reported"
    assert scoped_out[0]["verdict"] == "NOT_APPLICABLE"
    assert "Third Schedule" in " ".join(scoped_out[0]["gate_explanations"])


def test_a_result_carries_its_statistics_and_reasons(engagement_id: int) -> None:
    """A conclusion has to be reproducible from what the API returns."""
    created = client.post(
        f"/api/engagements/{engagement_id}/runs",
        json={"suite_ids": ["pii_retention"], "seed": 3},
    ).json()

    results = client.get(f"/api/runs/{created['id']}").json()["results"]

    assert results
    for row in results:
        assert "verdict" in row
        assert "gate_fired" in row
        assert "gate_reasons" in row
        assert "gate_remedies" in row
        assert "thresholds_applied" in row
        # The product's rule, enforced end to end rather than only in DDL.
        if row["verdict"] == "INSUFFICIENT_EVIDENCE":
            assert row["gate_reasons"], "a non-answer must explain itself"


def test_an_unknown_engagement_is_404(engagement_id: int) -> None:
    response = client.post(
        "/api/engagements/999999/runs", json={"suite_ids": ["consent"]}
    )

    assert response.status_code == 404


def test_an_unknown_run_is_404() -> None:
    assert client.get("/api/runs/999999").status_code == 404


def test_an_empty_suite_list_is_rejected(engagement_id: int) -> None:
    """Silently running nothing would report a clean, empty assessment."""
    response = client.post(
        f"/api/engagements/{engagement_id}/runs", json={"suite_ids": []}
    )

    assert response.status_code == 422


def test_the_available_suites_are_discoverable() -> None:
    """The console has to know what it may ask for. Registered procedures are
    the source of truth, not a list maintained by hand."""
    response = client.get("/api/suites")

    assert response.status_code == 200
    body = response.json()
    assert "suites" in body
    assert "registered_procedures" in body


def test_runs_are_listed_newest_first(engagement_id: int) -> None:
    client.post(
        f"/api/engagements/{engagement_id}/runs",
        json={"suite_ids": ["consent"], "seed": 11},
    )
    client.post(
        f"/api/engagements/{engagement_id}/runs",
        json={"suite_ids": ["consent"], "seed": 12},
    )

    response = client.get(f"/api/engagements/{engagement_id}/runs")

    assert response.status_code == 200
    runs = response.json()
    assert len(runs) >= 2
    assert runs[0]["id"] > runs[1]["id"]


# --- Latest result per control (the evidence viewer's source) --------------


@pytest.mark.usefixtures("seeded_estate")
def test_latest_result_carries_the_finding_and_the_evidence_hash(
    engagement_id: int,
) -> None:
    started = client.post(
        f"/api/engagements/{engagement_id}/runs",
        json={"suite_ids": ["third_party"], "seed": 42},
    )
    assert started.status_code == 201

    body = client.get("/api/controls/DPDP-TP-01/latest-result").json()
    assert body["run_id"] == started.json()["id"]
    assert body["verdict"] == "FAIL"
    assert body["detail"]["ranked"][0]["processor"] == "EchoScribe Transcription"

    [evidence] = body["evidence"]
    assert evidence["label"] == "third_parties"
    assert len(evidence["content_hash"]) == 64
    # The persisted summary must never carry a credential.
    assert "credential_token" not in str(evidence["summary"])


@pytest.mark.usefixtures("seeded_estate")
def test_the_erasure_cascade_reports_insufficient_evidence(engagement_id: int) -> None:
    client.post(
        f"/api/engagements/{engagement_id}/runs",
        json={"suite_ids": ["third_party"], "seed": 42},
    )
    body = client.get("/api/controls/DPDP-08-02/latest-result").json()

    assert body["verdict"] == "INSUFFICIENT_EVIDENCE"
    assert "G4_MISSING_ARTIFACT" in body["gate_reasons"]
    assert any("processor_erasure_instructions" in e for e in body["gate_explanations"])


def test_a_control_that_has_never_run_returns_null() -> None:
    """Not tested yet is a normal state, not an error. DPDP-03-01 is a
    documented control, so no run ever produces a result for it."""
    response = client.get("/api/controls/DPDP-03-01/latest-result")
    assert response.status_code == 200
    assert response.json() is None


def test_an_unknown_control_is_404() -> None:
    assert client.get("/api/controls/NOPE-00-00/latest-result").status_code == 404


def test_the_workpaper_downloads_as_a_docx(
    engagement_id: int, seeded_db: Session
) -> None:
    started = client.post(
        f"/api/engagements/{engagement_id}/runs",
        json={"suite_ids": ["pii_retention"], "seed": 42},
    )
    run_id = started.json()["id"]

    response = client.get(f"/api/runs/{run_id}/workpaper")

    assert response.status_code == 200
    assert response.headers["content-type"] == (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert f"run-{run_id}.docx" in response.headers["content-disposition"]
    # The ZIP local-file-header signature every OOXML document starts with.
    assert response.content[:2] == b"PK"

    logged = seeded_db.execute(
        text(
            "SELECT action FROM audit_log WHERE entity_type = 'test_run' "
            "AND entity_id = :run_id AND action = 'REPORT_EXPORTED'"
        ),
        {"run_id": str(run_id)},
    ).first()
    assert logged is not None


def test_the_workpaper_for_an_unknown_run_is_404() -> None:
    assert client.get("/api/runs/999999/workpaper").status_code == 404


def test_the_summary_downloads_as_a_docx(engagement_id: int) -> None:
    response = client.get(f"/api/engagements/{engagement_id}/summary")

    assert response.status_code == 200
    assert response.headers["content-type"] == (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert response.content[:2] == b"PK"


def test_the_summary_for_an_unknown_engagement_is_404() -> None:
    assert client.get("/api/engagements/999999/summary").status_code == 404
