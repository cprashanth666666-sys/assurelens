"""Synthetic identifiers must be checksum-valid and provably unissued.

Both halves matter. A detector tested only against malformed strings is not
tested; and a real-looking Aadhaar number in a public repository is
unacceptable however it was produced.
"""

from __future__ import annotations

import numpy as np
import pytest

from app.seed.identifiers import (
    is_synthetic_aadhaar,
    is_synthetic_pan,
    synthetic_aadhaar,
    synthetic_account_number,
    synthetic_email,
    synthetic_mobile,
    synthetic_pan,
    verhoeff_checksum,
    verhoeff_valid,
)


@pytest.mark.parametrize(
    "number",
    [
        # Published Verhoeff examples.
        "2363",
        "758722",
        "12345",
    ],
)
def test_verhoeff_accepts_its_own_output(number: str) -> None:
    assert verhoeff_valid(number + str(verhoeff_checksum(number)))


def test_verhoeff_rejects_a_single_digit_error() -> None:
    """The property a plain modulus check does not give you."""
    valid = "123456789012" [:-1]
    valid = valid + str(verhoeff_checksum(valid))
    assert verhoeff_valid(valid)

    for position in range(len(valid) - 1):
        for replacement in "0123456789":
            if replacement == valid[position]:
                continue
            corrupted = valid[:position] + replacement + valid[position + 1 :]
            assert not verhoeff_valid(corrupted), corrupted


def test_verhoeff_rejects_adjacent_transposition() -> None:
    base = "90876543210"
    valid = base + str(verhoeff_checksum(base))

    for i in range(len(valid) - 1):
        if valid[i] == valid[i + 1]:
            continue
        swapped = (
            valid[:i] + valid[i + 1] + valid[i] + valid[i + 2 :]
        )
        assert not verhoeff_valid(swapped), swapped


def test_generated_aadhaar_passes_verhoeff() -> None:
    rng = np.random.default_rng(42)
    for _ in range(200):
        number = synthetic_aadhaar(rng)
        assert len(number) == 12
        assert number.isdigit()
        assert verhoeff_valid(number)


def test_generated_aadhaar_is_outside_the_issued_range() -> None:
    """UIDAI issues numbers starting 2-9. These start 0, so they collide with
    nothing real while still satisfying a validating detector."""
    rng = np.random.default_rng(7)
    for _ in range(500):
        number = synthetic_aadhaar(rng)
        assert number[0] == "0"
        assert is_synthetic_aadhaar(number)


def test_generated_pan_matches_the_format_but_is_unallocated() -> None:
    """The fourth character is holder type; 'Z' is not an allocated value."""
    rng = np.random.default_rng(11)
    for _ in range(200):
        pan = synthetic_pan(rng)
        assert len(pan) == 10
        assert pan[:5].isalpha()
        assert pan[5:9].isdigit()
        assert pan[9].isalpha()
        assert pan[3] == "Z"
        assert is_synthetic_pan(pan)


def test_generated_mobile_matches_the_indian_format() -> None:
    rng = np.random.default_rng(13)
    for _ in range(200):
        mobile = synthetic_mobile(rng)
        assert len(mobile) == 10
        assert mobile[0] in "6789"
        assert mobile.isdigit()


def test_generated_email_uses_a_reserved_domain() -> None:
    """RFC 2606 reserves .test; nobody can register it, so nothing can be
    delivered to an address generated here."""
    rng = np.random.default_rng(17)
    for i in range(50):
        address = synthetic_email(rng, f"MFS{i:06d}")
        assert address.endswith(".test")


def test_account_numbers_share_a_fixed_issuer_prefix() -> None:
    rng = np.random.default_rng(19)
    for _ in range(50):
        assert synthetic_account_number(rng).startswith("9900")


def test_generation_is_deterministic_for_a_seed() -> None:
    """Reproducible runs are an audit requirement, not a convenience. [PRD P4]"""
    first = [synthetic_aadhaar(np.random.default_rng(42)) for _ in range(1)]
    second = [synthetic_aadhaar(np.random.default_rng(42)) for _ in range(1)]

    assert first == second
