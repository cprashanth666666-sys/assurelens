"""The target service carries its defects, and its working controls work.

These run against the service in-process. Suite 3 will probe the deployed one
over HTTP on Day 6; these exist so a defect cannot be silently "fixed" in the
meantime, which would make that suite pass while proving nothing.

Every test asserts the WRONG behaviour on purpose. A failure here means
someone repaired the system under test.
"""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# The target service's entry module is also called `app.py`, which collides
# with AssureLens's own `app` package. Loading it by path under a distinct
# name keeps the two apart without renaming either — and the collision is
# worth keeping, because the target has to look like an ordinary service.
TARGET_DIR = Path(__file__).resolve().parents[2] / "target_service"
sys.path.insert(0, str(TARGET_DIR))  # so its own `from defects import ...` works

_spec = importlib.util.spec_from_file_location(
    "target_service_app", TARGET_DIR / "app.py"
)
assert _spec and _spec.loader
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
target_app = _module.app

OPS = {"Authorization": "Bearer tok_ops_desk"}
VENDOR = {"Authorization": "Bearer tok_verifykart"}
STALE = {"Authorization": "Bearer tok_echoscribe"}
DEACTIVATED = {"Authorization": "Bearer tok_quillmark"}


@pytest.fixture
def target() -> Iterator[TestClient]:
    client = TestClient(target_app)
    client.post("/_probe/reset")
    yield client
    client.post("/_probe/reset")


# --- Labelling is a build requirement -------------------------------------


def test_root_declares_itself_vulnerable(target: TestClient) -> None:
    """Publishing a knowingly flawed service is only acceptable when it is
    unmistakably labelled and cannot reach anything real. [TRD 9]"""
    body = target.get("/").json()

    assert body["deliberately_vulnerable"] is True
    assert body["synthetic_data_only"] is True
    assert "never be deployed against a real system" in body["warning"]


# --- S2: ownership override -----------------------------------------------


def test_s2_vendor_reads_a_customer_it_does_not_own(target: TestClient) -> None:
    """VerifyKart is assigned customers 1001-1003 and reads 1040.

    Scope is checked and passes, so a reviewer reading the authorisation
    helper sees a control that works. The missing question is ownership.
    """
    response = target.get("/customers/1040", headers=VENDOR)

    assert response.status_code == 200, "defect S2 has been repaired"
    assert response.json()["account_number"], "full record exposed, not a stub"


def test_scope_check_itself_does_run(target: TestClient) -> None:
    """The contrast case. Without it, a passing probe would only show that
    nothing is checked at all."""
    response = target.post(
        "/customers/1001/spend-cap", json={"spend_cap": 100}, headers=VENDOR
    )

    assert response.status_code == 403


# --- S3: NaN bypasses the spend cap ---------------------------------------


def test_s3_honest_overflow_is_correctly_refused(target: TestClient) -> None:
    """Establishes that the cap check exists and works for real numbers."""
    response = target.post(
        "/customers/1001/spend-cap", json={"spend_cap": 999_999}, headers=OPS
    )

    assert response.status_code == 400


def test_s3_nan_passes_the_same_check(target: TestClient) -> None:
    """IEEE-754 defines every ordered comparison with NaN as false, so
    `value > cap` is false and the guard falls through to accept.

    One line, unbounded blast radius, and invisible to a reviewer scanning
    for logic errors: the comparison is the right way round.
    """
    response = target.post(
        "/customers/1001/spend-cap", json={"spend_cap": "NaN"}, headers=OPS
    )

    assert response.status_code == 200, "defect S3 has been repaired"
    assert response.json()["is_finite"] is False


@pytest.mark.parametrize("value", ["Infinity", "-Infinity"])
def test_s3_other_non_finite_values_also_slip_through(
    target: TestClient, value: str
) -> None:
    """-Infinity passes because it is genuinely below the cap; +Infinity is
    correctly refused. Recorded so the boundary probe expects the right
    answers rather than assuming all non-finite input behaves alike."""
    response = target.post(
        "/customers/1001/spend-cap", json={"spend_cap": value}, headers=OPS
    )

    expected = 400 if value == "Infinity" else 200
    assert response.status_code == expected


# --- S4: stale credential --------------------------------------------------


def test_s4_credential_unused_for_425_days_still_works(
    target: TestClient,
) -> None:
    """Probed on an endpoint EchoScribe holds scope for, so a 200 says
    plainly that a dormant credential authenticates. Probing an out-of-scope
    endpoint would return 403 and leave a reader unable to tell whether the
    credential was refused or merely misdirected."""
    response = target.get("/transcripts/MFS001001", headers=STALE)

    assert response.status_code == 200, "defect S4 has been repaired"
    assert response.json()["days_since_credential_last_used"] == 425


def test_deactivated_credential_is_refused(target: TestClient) -> None:
    """The contrast case: the authentication check does run."""
    assert target.get("/transcripts/MFS001001", headers=DEACTIVATED).status_code == 401


def test_missing_credential_is_refused(target: TestClient) -> None:
    assert target.get("/transcripts/MFS001001").status_code == 401


# --- Mass assignment -------------------------------------------------------


def test_profile_update_accepts_fields_it_should_not(target: TestClient) -> None:
    """No allowlist, so a caller can write its own role."""
    response = target.post("/profile", json={"role": "administrator"}, headers=VENDOR)

    assert response.status_code == 200
    assert response.json()["role"] == "administrator", "mass assignment repaired"


# --- S1: consent withdrawal does not reach the downstream -----------------


def test_s1_withdrawal_updates_the_store_but_not_the_segment(
    target: TestClient,
) -> None:
    """The record looks compliant and the principal keeps being marketed to.

    This is where privacy tooling most often fails silently, and why suite 2
    tests the downstream outcome rather than reading the consent table.
    """
    ref = "MFS001001"
    assert target.get(f"/marketing/segment/{ref}").json()["in_segment"] is True

    withdrawal = target.post(f"/consent/{ref}/withdraw")
    assert withdrawal.status_code == 200
    assert withdrawal.json()["consent_store_updated"] is True

    # The consent store is correct...
    assert target.get(f"/consent/{ref}").json()["status"] == "WITHDRAWN"
    # ...and the downstream has not heard about it.
    assert target.get(f"/marketing/segment/{ref}").json()["in_segment"] is True


def test_the_nightly_batch_does_eventually_fix_it(target: TestClient) -> None:
    """Which is why the finding is a latency, not an absence. The control
    exists; it is just too slow to satisfy s.6(6)."""
    ref = "MFS001002"
    target.post(f"/consent/{ref}/withdraw")
    target.post("/marketing/segment/refresh")

    assert target.get(f"/marketing/segment/{ref}").json()["in_segment"] is False


# --- s.6(6): withdrawal is harder than granting ---------------------------


def test_withdrawal_takes_more_effort_than_granting(target: TestClient) -> None:
    """Act s.6(6) requires withdrawal to be as easy as giving consent.
    Publishing both journeys makes that testable rather than arguable."""
    grant = target.get("/consent/journey/grant").json()
    withdraw = target.get("/consent/journey/withdraw").json()

    assert withdraw["steps"] > grant["steps"]
    assert len(withdraw["required_fields"]) > len(grant["required_fields"])
    assert len(withdraw["channels"]) < len(grant["channels"])


# --- P-08: refusals are not logged ----------------------------------------


def test_p08_refused_access_leaves_no_log_entry(target: TestClient) -> None:
    """The control on the control.

    Access control held — the request was refused — but nothing recorded the
    attempt, so review can never detect the pattern. Rule 6(1)(c) fails even
    though Rule 6(1)(b) held. A tool that only checks the 403 calls this a
    pass.
    """
    target.post("/_probe/reset")

    refused = target.post(
        "/customers/1001/spend-cap", json={"spend_cap": 100}, headers=VENDOR
    )
    assert refused.status_code == 403

    entries = target.get("/_probe/access-log").json()["entries"]
    assert not [e for e in entries if e["was_authorised"] is False], (
        "refusals are being logged; defect P-08 has been repaired"
    )


def test_authorised_access_is_logged(target: TestClient) -> None:
    """The contrast: logging works, it just skips the entries that matter."""
    target.post("/_probe/reset")
    target.get("/customers/1001", headers=OPS)

    entries = target.get("/_probe/access-log").json()["entries"]
    assert [e for e in entries if e["was_authorised"] is True]
