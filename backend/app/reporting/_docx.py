"""Shared DOCX styling for the workpaper and the executive summary.

One place for the brand colours and heading scale, so the two documents
can't silently drift apart the way two copies of the same styling code do.
"""

from __future__ import annotations

import datetime as dt

from docx.document import Document as DocumentT
from docx.shared import Pt, RGBColor

INK = RGBColor(0x0B, 0x0D, 0x12)
MUTED = RGBColor(0x55, 0x5B, 0x6B)


def apply_base_styles(doc: DocumentT, heading_sizes: dict[int, float]) -> None:
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = INK

    for level, size in heading_sizes.items():
        style = doc.styles[f"Heading {level}"]
        style.font.name = "Calibri"
        style.font.size = Pt(size)
        style.font.color.rgb = INK
        style.font.bold = True


def to_utc(value: dt.datetime) -> dt.datetime:
    """python-docx writes core-property timestamps with a literal "Z" without
    converting the value's own wall-clock time first -- so a tz-aware
    datetime that isn't already UTC would be mislabelled. Every date in
    this app is timezone-aware from the database, but this makes the
    conversion explicit rather than relying on the DB session always
    being UTC."""
    return value.astimezone(dt.UTC)
