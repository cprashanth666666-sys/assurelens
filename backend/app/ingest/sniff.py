"""MIME detection from content, not from the filename.

A client-declared MIME type or a `.pdf` extension is a claim, not a fact —
extraction routing that trusted the extension would let a renamed executable
walk through as a "PDF". Detection here is a small, dependency-free set of
magic-byte checks covering the formats this product's intake actually needs;
it deliberately does not attempt to be a general-purpose sniffer like
`python-magic` (which needs libmagic, a system dependency this project's
container images do not otherwise require).
"""

from __future__ import annotations

import zipfile
from io import BytesIO

_OOXML_PARTS = {
    "word/document.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xl/workbook.xml": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def sniff_mime(data: bytes) -> str | None:
    if data.startswith(b"%PDF-"):
        return "application/pdf"

    if data[:4] == b"PK\x03\x04":
        try:
            with zipfile.ZipFile(BytesIO(data)) as zf:
                names = set(zf.namelist())
        except zipfile.BadZipFile:
            return "application/zip"
        for part, mime in _OOXML_PARTS.items():
            if part in names:
                return mime
        return "application/zip"

    head = data[:2048].lstrip()
    lowered = head.lower()
    if lowered.startswith(b"<!doctype html") or lowered.startswith(b"<html"):
        return "text/html"

    try:
        text = data[:4096].decode("utf-8")
    except UnicodeDecodeError:
        return None

    stripped = text.lstrip()
    if stripped.startswith("<") and ("<html" in stripped.lower() or "<body" in stripped.lower()):
        return "text/html"

    # A CSV/plain-text file has no magic bytes at all. Decoding cleanly as
    # UTF-8 is the only signal available, so this is a fallback, not a first
    # match — every format with real magic bytes is checked above it.
    return "text/plain"
