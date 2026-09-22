"""Identifier detection.

Half of these tests are about what the detector must NOT report. False
positives in an assurance report are not a cosmetic problem: they are how a
client learns to stop reading one, and a scanner that flags every twelve-digit
number as a national identity number will be ignored within a week.
"""

from __future__ import annotations

import numpy as np
import pytest

from app.engine.detectors import (
    IdentifierClass,
    classes_present,
    detect_in_record,
    detect_in_text,
)
from app.seed.identifiers import (
    synthetic_aadhaar,
    synthetic_account_number,
    verhoeff_valid,
)


def classes(text: str) -> set[str]:
    return {d.identifier_class for d in detect_in_text(text)}


# --- Finds what is there ---------------------------------------------------


def test_finds_a_valid_aadhaar() -> None:
    number = synthetic_aadhaar(np.random.default_rng(42))

    assert IdentifierClass.AADHAAR in classes(f"my number is {number}")


@pytest.mark.parametrize("separator", [" ", "-"])
def test_finds_an_aadhaar_written_in_groups(separator: str) -> None:
    """People write them in fours. A detector that only matches an unbroken
    run finds the ones in a database and misses the ones typed by a human."""
    number = synthetic_aadhaar(np.random.default_rng(7))
    spaced = separator.join([number[:4], number[4:8], number[8:]])

    assert IdentifierClass.AADHAAR in classes(spaced)


def test_finds_a_pan() -> None:
    assert IdentifierClass.PAN in classes("PAN is ABCZE1234F please")


def test_finds_identifiers_in_free_text() -> None:
    """The identifier that matters is the one nobody meant to store.

    A customer reading their PAN aloud on a recorded call is not in a column
    called `pan`; it is in prose, in an asset that declares only transcript
    text. A column-aware scanner never sees it.
    """
    body = (
        "Agent: Could you confirm your PAN for verification? "
        "Customer: Yes, it is ABCZE1234F. Agent: Thank you."
    )

    assert IdentifierClass.PAN in classes(body)


def test_scans_values_not_field_names() -> None:
    """Trusting the name finds only the identifiers somebody remembered to
    label, which is the opposite of the problem."""
    record = {"free_text_note": "his PAN is ABCZE1234F"}

    assert any(
        d.identifier_class == IdentifierClass.PAN for d in detect_in_record(record)
    )


# --- Does NOT report what is not there -------------------------------------


def test_a_bank_account_is_not_an_aadhaar() -> None:
    """The regression that started this.

    Account numbers here are twelve digits, and roughly one arbitrary
    twelve-digit string in ten satisfies Verhoeff by chance -- a check digit
    is not an identity. Scanning 800 customer records reported 87 of them as
    Aadhaar numbers: an eleven per cent false-positive rate.
    """
    rng = np.random.default_rng(42)
    misread = 0

    for _ in range(800):
        account = synthetic_account_number(rng)
        found = classes(account)
        assert IdentifierClass.ACCOUNT_NUMBER in found
        if IdentifierClass.AADHAAR in found:
            misread += 1

    assert misread == 0, f"{misread}/800 account numbers reported as Aadhaar"


def test_the_collision_is_real_not_imagined() -> None:
    """Guards the guard: if account numbers stopped satisfying Verhoeff, the
    test above would pass for the wrong reason and stop protecting anything."""
    rng = np.random.default_rng(42)
    passing = sum(
        1 for _ in range(800) if verhoeff_valid(synthetic_account_number(rng))
    )

    assert passing > 20, (
        "account numbers no longer collide with Verhoeff, so the false-positive "
        "test is no longer exercising the case it was written for"
    )


def test_an_arbitrary_twelve_digit_number_needs_its_checksum() -> None:
    """Without Verhoeff every order reference becomes a national identifier."""
    assert IdentifierClass.AADHAAR not in classes("order 123456789012 shipped")


def test_the_holder_type_check_rejects_most_prose() -> None:
    """The fourth character is the holder type and only ten values are
    allocated, so most five-letter runs are excluded."""
    assert IdentifierClass.PAN not in classes("WORDS1234X is not a PAN")
    assert IdentifierClass.PAN not in classes("MIXED1234X is not a PAN")


def test_the_pan_detector_has_a_known_limit_and_it_is_stated() -> None:
    """A five-letter word whose fourth character happens to be an allocated
    holder type WILL match, and no amount of pattern work fixes that.

    "HELLO" has L in fourth position, which is the code for a local
    authority. The format simply does not carry enough information to rule it
    out, and a detector that claimed otherwise would be lying about its own
    precision.

    This is recorded rather than quietly tolerated because a PAN detection is
    reported as `verified`, and a reader is entitled to know what that word
    is worth: format-conformant, not identity-confirmed.
    """
    assert IdentifierClass.PAN in classes("HELLO1234X")

    detection = next(
        d for d in detect_in_text("HELLO1234X") if d.identifier_class == IdentifierClass.PAN
    )
    assert detection.verified is True, (
        "PAN verification means the format conforms, including the holder-type "
        "character -- it does not mean the value was confirmed against an "
        "issuing authority, and the workpaper should not imply that it was"
    )


def test_an_account_number_is_not_also_a_mobile() -> None:
    """Both are digit runs. The more specific class must win the characters,
    or one value gets reported twice under two different names."""
    found = classes(synthetic_account_number(np.random.default_rng(3)))

    assert IdentifierClass.ACCOUNT_NUMBER in found
    assert IdentifierClass.MOBILE not in found


def test_empty_and_absent_text_report_nothing() -> None:
    assert detect_in_text("") == []
    assert detect_in_record({"a": None, "b": 42}) == []


# --- Aggregation -----------------------------------------------------------


def test_classes_present_counts_occurrences() -> None:
    records = [
        {"note": "PAN ABCZE1234F"},
        {"note": "PAN ABCZE1234F and PQRZS5678K"},
    ]

    assert classes_present(records)[IdentifierClass.PAN] == 3


def test_a_verified_detection_is_marked_as_such() -> None:
    """A workpaper should distinguish a checksum-confirmed identifier from
    one whose shape merely matched."""
    number = synthetic_aadhaar(np.random.default_rng(11))
    detection = next(
        d for d in detect_in_text(number) if d.identifier_class == IdentifierClass.AADHAAR
    )

    assert detection.verified is True
