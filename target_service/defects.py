"""The planted defects, isolated in one module so they are impossible to miss.

Each function is a realistic implementation mistake, not a strawman. Every one
carries the control it violates and the reason it survives code review, because
the point of an adversarial test is to catch the class of fault that reads as
correct.

DO NOT "fix" anything here. These defects are the system under test. The
regression suite asserts they are findable; repairing one silently would make
the access-control suite pass while proving nothing.
"""

from __future__ import annotations

import math
from typing import Any

# --- S2: ownership check missing on one endpoint --------------------------
# Violates Rule 6(1)(b): "appropriate measures to control access to the
# computer resources used by such Data Fiduciary or such a Data Processor".
#
# The vendor service account is correctly scope-checked, and the scope check
# passes, so a reviewer reading the authorisation helper sees a control that
# works. What is missing is the second question: this principal holds
# read:customers, but is THIS customer one of theirs? Scope answers "may you
# read customers"; ownership answers "may you read this one".


def may_read_customer(principal: dict[str, Any], customer_id: int) -> bool:
    """Scope is checked. Ownership is not. That is the defect."""
    if "read:customers" not in principal["scopes"]:
        return False

    # A correct implementation continues:
    #     assigned = principal.get("assigned_customer_ids")
    #     if assigned is not None and customer_id not in assigned:
    #         return False
    return True


# --- S3: spend cap bypassed by NaN ----------------------------------------
# Violates Rule 6(1)(b): a limit that can be bypassed is not a measure
# controlling access.
#
# IEEE-754 defines every ordered comparison with NaN as false, so
# `value > cap` is false for NaN and the guard falls through to accept. One
# line, unbounded blast radius, and invisible to a reviewer scanning for
# logic errors -- the comparison is the right way round and reads correctly.


def exceeds_cap(value: float, cap: float) -> bool:
    """NaN makes this return False, so the caller accepts the request."""
    return value > cap


def cap_check_is_sound(value: float, cap: float) -> bool:
    """What the check should have been, kept for the fix demonstration."""
    if not math.isfinite(value):
        return False
    return not exceeds_cap(value, cap)


# --- S4: stale credential still authenticates ------------------------------
# Violates Rule 6(1)(b) and 6(1)(c). The token is validated for existence and
# for being marked active, but never against last use. A processor that
# stopped working with you fourteen months ago still holds a working key.

STALE_CREDENTIAL_DAYS = 180


def credential_is_accepted(record: dict[str, Any]) -> bool:
    """Existence and active flag are checked. Last use is not."""
    if record is None:
        return False
    if not record.get("is_active"):
        return False

    # A correct implementation continues:
    #     if record["days_since_last_use"] > STALE_CREDENTIAL_DAYS:
    #         return False
    return True


# --- P-08: unauthorised access is refused but not logged -------------------
# Violates Rule 6(1)(c): "visibility on the accessing of such personal data,
# through appropriate logs, monitoring and review, for enabling detection of
# unauthorised access".
#
# This is the control on the control. Access control held -- the request was
# refused -- but nothing recorded the attempt, so review can never detect the
# pattern. A tool that only checks whether the 403 was returned calls this a
# pass.


def should_log(authorised: bool) -> bool:
    """Only successful access is recorded. Refusals vanish."""
    return authorised


# --- Mass assignment -------------------------------------------------------
# Violates Rule 6(1)(b). The profile update copies whatever the body contains
# onto the stored record, so a caller can set fields the API never intended to
# expose -- including its own role.

PROTECTED_PROFILE_FIELDS = frozenset({"role", "scopes", "is_admin", "customer_ids"})


def apply_profile_update(
    stored: dict[str, Any], submitted: dict[str, Any]
) -> dict[str, Any]:
    """Every submitted key is written. No allowlist is applied."""
    updated = dict(stored)
    for key, value in submitted.items():
        # A correct implementation continues:
        #     if key in PROTECTED_PROFILE_FIELDS:
        #         continue
        updated[key] = value
    return updated
