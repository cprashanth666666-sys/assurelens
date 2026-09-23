"""Meridian customer API — DELIBERATELY VULNERABLE TARGET SERVICE.

This is not AssureLens. It is the *system under test*: a stand-in for a client
application, carrying intentional defects that the access-control suite probes
over HTTP. Read README.md before touching anything here.

Why a separate process rather than in-process fixtures: a defect that is not
reachable over the network should not be found, exactly as in reality. The
suite authenticates and probes this service the way an external tester would,
so its evidence is a real request/response pair, and if the service is down
the gate fires G8_TARGET_UNREACHABLE rather than silently passing.
[docs/TRD.md 1.2]

Safety: synthetic data only, no database credentials, no route to anything
real, and the root endpoint says so.
"""

from __future__ import annotations

import copy
import logging
import math
import os
from typing import Any

from fastapi import Body, FastAPI, Header, HTTPException, Path
from pydantic import BaseModel

from defects import (
    apply_profile_update,
    credential_is_accepted,
    exceeds_cap,
    may_read_customer,
    should_log,
)

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
log = logging.getLogger("target")

WARNING = (
    "This service is deliberately vulnerable and exists only as a test target "
    "for AssureLens. It holds synthetic data, has no database credentials, and "
    "must never be deployed against a real system."
)

app = FastAPI(
    title="Meridian Customer API (deliberately vulnerable test target)",
    description=WARNING,
    version="0.2.0",
)

# --- Synthetic state -------------------------------------------------------
# Small, fixed, and in memory. The estate proper lives in the AssureLens
# database; this service only needs enough to make the probes meaningful.

SPEND_CAP = 50_000.0

PRINCIPALS: dict[str, dict[str, Any]] = {
    # The bank's own staff account: correctly scoped, owns everything.
    "tok_ops_desk": {
        "name": "user_ops_desk",
        "scopes": ["read:customers", "write:customers"],
        "assigned_customer_ids": None,  # None means "all"
        "is_active": True,
        "days_since_last_use": 1,
        "role": "operations",
    },
    # KYC vendor: should only reach the customers it verifies. Defect S2 lets
    # it reach every customer.
    "tok_verifykart": {
        "name": "VerifyKart KYC",
        "scopes": ["read:customers", "read:kyc"],
        "assigned_customer_ids": [1001, 1002, 1003],
        "is_active": True,
        "days_since_last_use": 2,
        "role": "processor",
    },
    # Defect S4: last used 425 days ago and still accepted.
    "tok_echoscribe": {
        "name": "EchoScribe Transcription",
        "scopes": ["read:transcripts"],
        "assigned_customer_ids": [],
        "is_active": True,
        "days_since_last_use": 425,
        "role": "processor",
    },
    # Correctly deactivated: the comparison case, so a passing probe proves
    # the check runs rather than that nothing is checked.
    "tok_quillmark": {
        "name": "Quillmark Surveys",
        "scopes": ["read:customers"],
        "assigned_customer_ids": [],
        "is_active": False,
        "days_since_last_use": 120,
        "role": "processor",
    },
}

# Snapshot for /_probe/reset. POST /profile mutates these records in place --
# that is the mass-assignment defect -- so without restoring them a probe run
# that escalates a role would leave the escalated role in place for the next
# run, and two runs with the same seed would stop agreeing.
_PRINCIPALS_AT_START = copy.deepcopy(PRINCIPALS)

CUSTOMERS: dict[int, dict[str, Any]] = {
    cid: {
        "customer_id": cid,
        "external_ref": f"MFS{cid:06d}",
        "name": f"Customer {cid}",
        "account_number": f"9900{cid:08d}",
        "spend_cap": SPEND_CAP,
    }
    for cid in range(1001, 1051)
}

MARKETING_SEGMENT: set[str] = {c["external_ref"] for c in CUSTOMERS.values()}
CONSENT: dict[str, str] = {ref: "ACTIVE" for ref in MARKETING_SEGMENT}

# Written only when should_log() says so, which is the P-08 defect.
ACCESS_LOG: list[dict[str, Any]] = []


def _record(actor: str, action: str, authorised: bool) -> None:
    if should_log(authorised):
        ACCESS_LOG.append(
            {"actor_ref": actor, "action": action, "was_authorised": authorised}
        )


def _authenticate(token: str | None) -> dict[str, Any]:
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    record = PRINCIPALS.get(token.removeprefix("Bearer ").strip())
    if not credential_is_accepted(record):  # type: ignore[arg-type]
        raise HTTPException(status_code=401, detail="Credential not accepted")
    return record  # type: ignore[return-value]


# --- Models ----------------------------------------------------------------


class Root(BaseModel):
    service: str
    warning: str
    synthetic_data_only: bool
    deliberately_vulnerable: bool


class FormDescriptor(BaseModel):
    """Step count and required fields for a journey.

    Act s.6(6) requires withdrawal to be as easy as granting. Publishing both
    journeys makes that testable rather than a matter of opinion.
    """

    steps: int
    required_fields: list[str]
    channels: list[str]


# --- Endpoints -------------------------------------------------------------


@app.get("/", response_model=Root)
def root() -> Root:
    """Unmistakable labelling is a build requirement, not a nicety. [TRD 9]"""
    return Root(
        service="Meridian Customer API — TEST TARGET",
        warning=WARNING,
        synthetic_data_only=True,
        deliberately_vulnerable=True,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/customers/{customer_id}")
def get_customer(
    customer_id: int = Path(...),
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """Defect S2: scope is checked, ownership is not."""
    principal = _authenticate(authorization)

    allowed = may_read_customer(principal, customer_id)
    if not allowed:
        _record(principal["name"], f"READ customer {customer_id}", False)
        raise HTTPException(status_code=403, detail="Not permitted")

    customer = CUSTOMERS.get(customer_id)
    if customer is None:
        _record(principal["name"], f"READ customer {customer_id}", True)
        raise HTTPException(status_code=404, detail="No such customer")

    _record(principal["name"], f"READ customer {customer_id}", True)
    return customer


@app.post("/customers/{customer_id}/spend-cap")
def set_spend_cap(
    customer_id: int = Path(...),
    body: dict[str, Any] = Body(...),
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """Defect S3: NaN passes the cap check, because NaN > x is always false."""
    principal = _authenticate(authorization)
    if "write:customers" not in principal["scopes"]:
        _record(principal["name"], f"WRITE spend-cap {customer_id}", False)
        raise HTTPException(status_code=403, detail="Not permitted")

    customer = CUSTOMERS.get(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="No such customer")

    raw = body.get("spend_cap")
    try:
        requested = float(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="spend_cap must be a number") from None

    if exceeds_cap(requested, SPEND_CAP):
        raise HTTPException(status_code=400, detail="spend_cap exceeds the limit")

    customer["spend_cap"] = requested
    _record(principal["name"], f"WRITE spend-cap {customer_id}", True)
    return {
        "customer_id": customer_id,
        "spend_cap": requested,
        "is_finite": math.isfinite(requested),
    }


@app.get("/transcripts/{external_ref}")
def get_transcript(
    external_ref: str,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """Defect S4 is cleanest here.

    EchoScribe holds read:transcripts and has not used its credential in 425
    days. Probing an endpoint it lacks scope for would return 403 and muddy
    the evidence -- a reader could not tell whether the stale credential was
    refused or merely out of scope. Here a 200 says plainly that a credential
    dormant for over a year still works.
    """
    principal = _authenticate(authorization)
    if "read:transcripts" not in principal["scopes"]:
        _record(principal["name"], f"READ transcript {external_ref}", False)
        raise HTTPException(status_code=403, detail="Not permitted")

    _record(principal["name"], f"READ transcript {external_ref}", True)
    return {
        "external_ref": external_ref,
        "body": "Agent: How can I help today? Customer: I would like to check my statement.",
        "accessed_by": principal["name"],
        "days_since_credential_last_used": principal["days_since_last_use"],
    }


@app.post("/profile")
def update_profile(
    body: dict[str, Any] = Body(...),
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """Mass assignment: every submitted key is written, role included."""
    principal = _authenticate(authorization)
    updated = apply_profile_update(principal, body)
    principal.update(updated)
    return {"name": principal["name"], "role": principal["role"],
            "scopes": principal["scopes"]}


@app.get("/consent/{external_ref}")
def get_consent(external_ref: str) -> dict[str, Any]:
    return {"external_ref": external_ref,
            "status": CONSENT.get(external_ref, "UNKNOWN")}


@app.post("/consent/{external_ref}/withdraw")
def withdraw_consent(external_ref: str) -> dict[str, Any]:
    """The consent store updates immediately.

    The marketing segment does not: it refreshes on the nightly batch, so the
    principal stays in it. That gap is defect S1, and it is why suite 2 tests
    the downstream outcome rather than the consent record.
    """
    if external_ref not in CONSENT:
        raise HTTPException(status_code=404, detail="No such principal")

    CONSENT[external_ref] = "WITHDRAWN"
    # MARKETING_SEGMENT is deliberately NOT updated here.
    return {"external_ref": external_ref, "status": "WITHDRAWN",
            "consent_store_updated": True}


@app.get("/marketing/segment/{external_ref}")
def in_marketing_segment(external_ref: str) -> dict[str, Any]:
    """What the downstream system actually believes right now."""
    return {"external_ref": external_ref,
            "in_segment": external_ref in MARKETING_SEGMENT}


@app.post("/marketing/segment/refresh")
def refresh_segment() -> dict[str, Any]:
    """The nightly batch, exposed so a fix can be demonstrated."""
    withdrawn = {ref for ref, status in CONSENT.items() if status == "WITHDRAWN"}
    removed = len(MARKETING_SEGMENT & withdrawn)
    MARKETING_SEGMENT.difference_update(withdrawn)
    return {"removed": removed, "segment_size": len(MARKETING_SEGMENT)}


@app.get("/consent/journey/{action}", response_model=FormDescriptor)
def consent_journey(action: str) -> FormDescriptor:
    """Grant and withdrawal journeys, for the s.6(6) effort-parity test."""
    if action == "grant":
        return FormDescriptor(
            steps=1,
            required_fields=["external_ref"],
            channels=["web", "app", "ivr"],
        )
    if action == "withdraw":
        # Harder than granting: more steps, more fields, fewer channels.
        return FormDescriptor(
            steps=3,
            required_fields=["external_ref", "account_number", "reason_code"],
            channels=["web"],
        )
    raise HTTPException(status_code=404, detail="Unknown journey")


@app.get("/_probe/access-log")
def read_access_log() -> dict[str, Any]:
    """Exposes what the service recorded, so P-08 can compare attempts made
    against attempts logged. Present for testability; a real system would be
    queried through its logging stack."""
    return {"entries": ACCESS_LOG, "count": len(ACCESS_LOG)}


@app.post("/_probe/reset")
def reset_state() -> dict[str, str]:
    """Restore the in-memory state so probe runs are independent."""
    ACCESS_LOG.clear()
    for token, record in _PRINCIPALS_AT_START.items():
        PRINCIPALS[token] = copy.deepcopy(record)
    MARKETING_SEGMENT.clear()
    MARKETING_SEGMENT.update(c["external_ref"] for c in CUSTOMERS.values())
    for ref in CONSENT:
        CONSENT[ref] = "ACTIVE"
    for cid, customer in CUSTOMERS.items():
        customer["spend_cap"] = SPEND_CAP
    return {"status": "reset"}
