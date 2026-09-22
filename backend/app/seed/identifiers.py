"""Synthetic Indian identifiers for the generated estate.

These have to be **format-valid and checksum-valid**, because a PII detector
tested only against malformed strings is not tested at all — it would pass
while being unable to recognise anything real.

They also have to be **provably not real**, because this repository is
public. A real-looking Aadhaar number in a public repo is unacceptable
regardless of how it was produced.

Both are satisfied by drawing from ranges the issuing authorities do not
allocate:

* UIDAI does not issue Aadhaar numbers beginning 0 or 1, so every number
  generated here starts with 0 and can never collide with a live one, while
  still satisfying the Verhoeff checksum a detector validates.
* PAN's fourth character encodes holder type from a fixed set; 'Z' is not in
  it, so a PAN shaped here matches the regex and belongs to no one.
"""

from __future__ import annotations

import numpy as np

# --- Verhoeff -------------------------------------------------------------
# UIDAI uses the Verhoeff scheme for the Aadhaar check digit. It catches all
# single-digit errors and all adjacent transpositions, which a simple modulus
# does not — which is why a detector that merely counts twelve digits will
# happily flag any twelve-digit number as an Aadhaar.

_D = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 2, 3, 4, 0, 6, 7, 8, 9, 5),
    (2, 3, 4, 0, 1, 7, 8, 9, 5, 6),
    (3, 4, 0, 1, 2, 8, 9, 5, 6, 7),
    (4, 0, 1, 2, 3, 9, 5, 6, 7, 8),
    (5, 9, 8, 7, 6, 0, 4, 3, 2, 1),
    (6, 5, 9, 8, 7, 1, 0, 4, 3, 2),
    (7, 6, 5, 9, 8, 2, 1, 0, 4, 3),
    (8, 7, 6, 5, 9, 3, 2, 1, 0, 4),
    (9, 8, 7, 6, 5, 4, 3, 2, 1, 0),
)

_P = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 5, 7, 6, 2, 8, 3, 0, 9, 4),
    (5, 8, 0, 3, 7, 9, 6, 1, 4, 2),
    (8, 9, 1, 6, 0, 4, 3, 5, 2, 7),
    (9, 4, 5, 3, 1, 2, 6, 8, 7, 0),
    (4, 2, 8, 6, 5, 7, 3, 9, 0, 1),
    (2, 7, 9, 3, 8, 0, 6, 4, 1, 5),
    (7, 0, 4, 6, 9, 1, 3, 2, 5, 8),
)

_INV = (0, 4, 3, 2, 1, 5, 6, 7, 8, 9)


def verhoeff_checksum(digits: str) -> int:
    """Check digit that makes `digits + result` a valid Verhoeff string."""
    c = 0
    for i, ch in enumerate(reversed(digits), start=1):
        c = _D[c][_P[i % 8][int(ch)]]
    return _INV[c]


def verhoeff_valid(number: str) -> bool:
    """True when the final digit is the correct Verhoeff check digit."""
    if not number.isdigit():
        return False
    c = 0
    for i, ch in enumerate(reversed(number)):
        c = _D[c][_P[i % 8][int(ch)]]
    return c == 0


# --- Generators -----------------------------------------------------------

# UIDAI allocates Aadhaar numbers starting 2-9. Anything beginning 0 or 1 is
# outside the issued space, so these are unmistakably synthetic.
_AADHAAR_RESERVED_FIRST_DIGIT = "0"

# PAN's fourth character is the holder type: P individual, C company,
# H HUF, F firm, A AOP, T trust, B BOI, L local authority, J artificial
# juridical person, G government. 'Z' is not allocated.
_PAN_RESERVED_HOLDER_TYPE = "Z"

_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def synthetic_aadhaar(rng: np.random.Generator) -> str:
    """Twelve digits, Verhoeff-valid, in the unissued 0-prefixed space."""
    body = _AADHAAR_RESERVED_FIRST_DIGIT + "".join(
        str(d) for d in rng.integers(0, 10, size=10)
    )
    return body + str(verhoeff_checksum(body))


def synthetic_pan(rng: np.random.Generator) -> str:
    """AAAAA9999A shape, with an unallocated holder-type character."""
    head = "".join(_LETTERS[i] for i in rng.integers(0, 26, size=3))
    surname_initial = _LETTERS[int(rng.integers(0, 26))]
    digits = "".join(str(d) for d in rng.integers(0, 10, size=4))
    check = _LETTERS[int(rng.integers(0, 26))]
    return f"{head}{_PAN_RESERVED_HOLDER_TYPE}{surname_initial}{digits}{check}"


def synthetic_mobile(rng: np.random.Generator) -> str:
    """Indian mobile shape: first digit 6-9, ten digits total."""
    first = str(int(rng.integers(6, 10)))
    rest = "".join(str(d) for d in rng.integers(0, 10, size=9))
    return first + rest


def synthetic_email(rng: np.random.Generator, external_ref: str) -> str:
    """Addresses use .test, which RFC 2606 reserves and nobody can register."""
    domain = ("example.test", "mail.test", "inbox.test")[int(rng.integers(0, 3))]
    return f"{external_ref.lower()}@{domain}"


def synthetic_account_number(rng: np.random.Generator) -> str:
    """Bank account: a fixed issuer prefix and eight digits."""
    return "9900" + "".join(str(d) for d in rng.integers(0, 10, size=8))


def is_synthetic_aadhaar(number: str) -> bool:
    """Guard used by tests: nothing issued may reach the repository."""
    return number.startswith(_AADHAAR_RESERVED_FIRST_DIGIT)


def is_synthetic_pan(pan: str) -> bool:
    return len(pan) == 10 and pan[3] == _PAN_RESERVED_HOLDER_TYPE
