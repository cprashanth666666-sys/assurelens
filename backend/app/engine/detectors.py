"""Identifier detection.

Used by suite 1 to establish what an asset actually holds, which is then
compared against what its inventory declares. The gap is the finding.

Two properties matter more than coverage of exotic formats:

**Checksums where a checksum exists.** A detector that flags any twelve
digits as an Aadhaar will report a transaction reference, an order number and
a phone number with a country code. False positives in an assurance report
are not a minor annoyance -- they are how a client learns to ignore it.

**Free text, not just columns.** The identifier that matters is the one
nobody intended to store, and it is in prose: a customer reading their PAN
aloud on a recorded call. A column-aware scanner never sees it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.seed.identifiers import verhoeff_valid


class IdentifierClass:
    AADHAAR = "aadhaar"
    PAN = "pan"
    MOBILE = "mobile"
    EMAIL = "email"
    ACCOUNT_NUMBER = "account_number"
    NAME = "name"


# --- Patterns --------------------------------------------------------------
# Word boundaries throughout: without them a PAN pattern matches inside a
# longer token and a mobile pattern matches part of an account number.

_PAN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
_AADHAAR = re.compile(r"\b(\d{4}[ -]?\d{4}[ -]?\d{4})\b")
_MOBILE = re.compile(r"\b[6-9]\d{9}\b")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_ACCOUNT = re.compile(r"\b9900\d{8}\b")

# PAN's fourth character is the holder type. Only these are allocated, so a
# five-letter run with anything else there is not a PAN -- which is what
# keeps ordinary words in prose from matching.
_PAN_HOLDER_TYPES = frozenset("PCHFATBLJG")

# The synthetic corpus uses Z, a value the authority does not allocate. It is
# accepted here so the detector can be exercised against data that is
# format-valid and provably not real.
_SYNTHETIC_HOLDER_TYPE = "Z"


@dataclass(frozen=True)
class Detection:
    identifier_class: str
    value: str
    field: str
    # Whether a checksum or structural rule confirmed it, as opposed to the
    # shape merely matching. A workpaper should distinguish the two.
    verified: bool


def _claimed(spans: list[tuple[int, int]], start: int, end: int) -> bool:
    return any(start < s_end and end > s_start for s_start, s_end in spans)


def _detect_pan(
    text: str, field: str, spans: list[tuple[int, int]]
) -> list[Detection]:
    found = []
    for match in _PAN.finditer(text):
        value = match.group(0)
        holder = value[3]
        if holder not in _PAN_HOLDER_TYPES and holder != _SYNTHETIC_HOLDER_TYPE:
            continue
        if _claimed(spans, *match.span()):
            continue
        spans.append(match.span())
        found.append(Detection(IdentifierClass.PAN, value, field, verified=True))
    return found


def _detect_aadhaar(
    text: str, field: str, spans: list[tuple[int, int]]
) -> list[Detection]:
    """Twelve digits are not an Aadhaar number until Verhoeff says so -- and
    not even then if a more specific class already claimed them.

    Verhoeff catches every single-digit error and every adjacent
    transposition, but roughly one arbitrary twelve-digit string in ten
    satisfies it by chance. That is not a defect in the scheme: it is a check
    digit, not an identity. Running it over a corpus of twelve-digit bank
    account numbers reported 87 of 800 as Aadhaar numbers -- a false-positive
    rate of eleven per cent, in an assurance report, which is how a client
    learns to stop reading one.

    Span exclusion is what fixes it. An account number is recognised by a
    known issuer prefix, which is stronger evidence than a checksum that one
    value in ten passes anyway.
    """
    found = []
    for match in _AADHAAR.finditer(text):
        digits = re.sub(r"[ -]", "", match.group(1))
        if len(digits) != 12 or not verhoeff_valid(digits):
            continue
        if _claimed(spans, *match.span()):
            continue
        spans.append(match.span())
        found.append(Detection(IdentifierClass.AADHAAR, digits, field, verified=True))
    return found


def _detect_simple(
    pattern: re.Pattern[str],
    identifier_class: str,
    text: str,
    field: str,
    spans: list[tuple[int, int]],
    verified: bool = False,
) -> list[Detection]:
    found = []
    for match in pattern.finditer(text):
        if _claimed(spans, *match.span()):
            continue
        spans.append(match.span())
        found.append(
            Detection(identifier_class, match.group(0), field, verified=verified)
        )
    return found


def detect_in_text(text: str, field: str = "") -> list[Detection]:
    """Every identifier in a string, most specific class first.

    Order is the whole design. Several patterns match overlapping runs of
    digits, and whichever runs first wins the characters. Sorting by how much
    evidence each pattern actually carries -- structure, then a known issuer
    prefix, then a checksum, then a bare shape -- is what keeps a bank account
    number from being reported as somebody's national identity number.
    """
    if not text:
        return []

    spans: list[tuple[int, int]] = []
    detections: list[Detection] = []

    # Unambiguous structure: nothing else looks like this.
    detections.extend(
        _detect_simple(_EMAIL, IdentifierClass.EMAIL, text, field, spans)
    )
    # Letters, digits, letter, with a constrained holder-type character.
    detections.extend(_detect_pan(text, field, spans))
    # A known issuer prefix is stronger evidence than a check digit that one
    # value in ten satisfies by accident.
    detections.extend(
        _detect_simple(
            _ACCOUNT, IdentifierClass.ACCOUNT_NUMBER, text, field, spans,
            verified=True,
        )
    )
    # Checksum-validated, over whatever digits remain unclaimed.
    detections.extend(_detect_aadhaar(text, field, spans))
    # Weakest: any ten digits beginning 6-9.
    detections.extend(
        _detect_simple(_MOBILE, IdentifierClass.MOBILE, text, field, spans)
    )

    return detections


def detect_in_record(content: dict[str, Any]) -> list[Detection]:
    """Every identifier in a record, scanning values rather than field names.

    A field called `body` holds whatever was said on the call; a field called
    `notes` holds whatever someone typed. Trusting the name would mean
    finding only the identifiers somebody remembered to label.
    """
    detections: list[Detection] = []
    for field, value in content.items():
        if isinstance(value, str):
            detections.extend(detect_in_text(value, field))
        elif isinstance(value, dict):
            detections.extend(detect_in_record(value))
    return detections


def classes_present(records: list[dict[str, Any]]) -> dict[str, int]:
    """Identifier classes across records, with a count for each."""
    counts: dict[str, int] = {}
    for record in records:
        for detection in detect_in_record(record):
            counts[detection.identifier_class] = (
                counts.get(detection.identifier_class, 0) + 1
            )
    return counts
