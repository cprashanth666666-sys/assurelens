"""Test suites.

Importing this package registers every procedure and evidence source. The
engine resolves a control's declared plugin key against that registry, so a
suite that is never imported is a control that silently never runs -- which
is why the import lives here rather than being left to a caller to remember.
"""

from app.suites import ai_assurance, consent, evidence_sources, pii_retention, third_party

__all__ = ["ai_assurance", "consent", "evidence_sources", "pii_retention", "third_party"]
