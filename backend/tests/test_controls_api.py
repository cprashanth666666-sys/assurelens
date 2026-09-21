"""Control library API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.usefixtures("seeded_db")

client = TestClient(app)


def test_list_returns_the_whole_library() -> None:
    rows = client.get("/api/controls").json()

    assert len(rows) == 25
    assert rows == sorted(rows, key=lambda r: r["ref"])


def test_filter_by_domain() -> None:
    rows = client.get("/api/controls", params={"domain": "AI_GOVERNANCE"}).json()

    assert len(rows) == 3
    assert all(r["domain"] == "AI_GOVERNANCE" for r in rows)


def test_filter_by_executable() -> None:
    rows = client.get("/api/controls", params={"executable": True}).json()

    assert len(rows) == 13
    assert all(r["suite"] for r in rows)


def test_filter_by_framework_finds_cross_references() -> None:
    """A client already running ISO 27001 wants to see what they can reuse."""
    rows = client.get("/api/controls", params={"framework": "ISO27001"}).json()

    assert rows
    assert all("ISO27001" in r["framework_refs"] for r in rows)


def test_filter_by_scope_surfaces_the_excluded_control() -> None:
    rows = client.get("/api/controls", params={"in_scope": False}).json()

    assert len(rows) == 1
    assert rows[0]["ref"] == "DPDP-08-04"
    assert "Third Schedule" in rows[0]["na_reason"]


def test_detail_leads_with_the_legal_basis() -> None:
    """Primary clause first, so the reader sees what the control rests on."""
    detail = client.get("/api/controls/DPDP-06-02").json()

    assert detail["clauses"][0]["is_primary"] is True
    assert detail["clauses"][0]["ref"] == "R6(1)(b)"
    assert detail["primary_clause"] == "R6(1)(b)"


def test_detail_carries_verbatim_statutory_text() -> None:
    """The reader sees the statute, not a paraphrase. [UX 4.3]"""
    detail = client.get("/api/controls/DPDP-06-02").json()
    primary = detail["clauses"][0]

    assert "appropriate measures to control access" in primary["verbatim_text"]
    assert primary["source_status"] == "VERIFIED"
    assert primary["rationale"]


def test_unverified_iso_reference_does_not_flag_the_control() -> None:
    """G7_SOURCE_UNVERIFIED acts on the PRIMARY clause only.

    DPDP-06-02 cites unverified ISO controls alongside a DPDP provision read
    from the gazette. Letting an unpurchased standard's cross-reference gate a
    control with a sound legal basis would make the gate meaningless.
    """
    detail = client.get("/api/controls/DPDP-06-02").json()

    iso = [c for c in detail["clauses"] if c["framework_code"] == "ISO27001"]
    assert iso
    assert all(c["source_status"] == "UNVERIFIED" for c in iso)
    assert detail["primary_source_unverified"] is False


def test_control_with_an_unverified_primary_clause_is_flagged() -> None:
    """Rule 15 defines its obligation by reference to a government order that
    may not have been issued, so there is nothing concrete to test against."""
    detail = client.get("/api/controls/DPDP-15-01").json()

    assert detail["primary_source_unverified"] is True
    assert detail["clauses"][0]["source_note"]


def test_executable_control_exposes_its_evidence_contract() -> None:
    detail = client.get("/api/controls/DPDP-03-03").json()

    assert detail["is_executable"] is True
    assert detail["plugin_key"] == "consent.withdrawal_propagation"
    assert "consent_records" in str(detail["evidence_contract"])


def test_unknown_control_is_404() -> None:
    assert client.get("/api/controls/DPDP-99-99").status_code == 404


def test_engagement_summary() -> None:
    body = client.get("/api/engagement").json()

    assert body["organization"] == "Meridian Financial Services India GCC"
    assert body["compliance_deadline"] == "2027-05-13"
    assert body["is_significant_data_fiduciary"] is True
    # Drives the standing synthetic-data disclosure in the UI.
    assert body["is_synthetic"] is True
    assert body["control_count"] == 25
    assert body["executable_count"] == 13
    assert body["out_of_scope_count"] == 1
