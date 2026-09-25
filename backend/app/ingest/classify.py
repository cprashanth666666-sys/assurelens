"""Relevancy classification: what kind of DPDP-relevant document is this.

Two stages, cheapest first:

1. A keyword/heuristic pass — deterministic, free, and auditable (the
   `reasoning` field says exactly which phrases matched). Handles the large
   majority of real submissions, whose titles and section headers are not
   subtle.
2. Nothing beyond that yet. An LLM fallback for the heuristic's low-confidence
   cases is a natural next step, but it means treating the document's own text
   as untrusted input to that call (a document can contain prompt-injection
   text aimed at its own classifier) and is deliberately left for a follow-up
   rather than bolted on here.

Consistent with this product's central argument: a document the heuristic
cannot confidently place is reported as UNRECOGNIZED with low confidence, not
silently forced into the nearest category. A wrong confident label is worse
than an honest "not sure" — the same reasoning the evidence-sufficiency gate
applies to test verdicts applies here to document intake.
"""

from __future__ import annotations

from dataclasses import dataclass

CATEGORY_UNRECOGNIZED = "UNRECOGNIZED"

# Ordered by specificity: a document matching several is labelled by whichever
# category scores highest, so a "vendor DPA" that happens to mention "consent"
# in passing is not misfiled as a consent form.
_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "PRIVACY_NOTICE": [
        "privacy notice", "privacy policy", "notice under section",
        "personal data we collect", "data principal", "purpose of processing",
    ],
    "CONSENT_FORM": [
        "consent form", "i consent", "withdraw consent", "consent manager",
        "i hereby consent", "grant of consent",
    ],
    "DPIA": [
        "data protection impact assessment", "dpia", "risk to data principals",
        "necessity and proportionality",
    ],
    "VENDOR_DPA": [
        "data processing agreement", "processor agreement", "sub-processor",
        "data processor", "third party agreement", "standard contractual clauses",
    ],
    "BREACH_RUNBOOK": [
        "breach response", "incident response plan", "breach notification",
        "intimation of personal data breach", "breach runbook",
    ],
    "SECURITY_POLICY": [
        "information security policy", "access control policy", "encryption standard",
        "security safeguards", "isms", "iso/iec 27001", "iso 27001",
    ],
    "RETENTION_POLICY": [
        "retention schedule", "retention policy", "erasure policy",
        "data retention period", "third schedule",
    ],
    "GRIEVANCE_PROCEDURE": [
        "grievance redressal", "grievance officer", "grievance procedure",
        "ninety days", "90 days",
    ],
}

# Below this, the label is reported as UNRECOGNIZED rather than the
# highest-scoring category — a weak match is not a confident finding.
MIN_CONFIDENT_SCORE = 2


@dataclass
class ClassificationResult:
    category: str
    confidence: float
    method: str
    reasoning: str


def classify_text(text: str | None) -> ClassificationResult:
    if not text or not text.strip():
        return ClassificationResult(
            category=CATEGORY_UNRECOGNIZED,
            confidence=0.0,
            method="keyword_heuristic",
            reasoning="No extractable text.",
        )

    lowered = text.lower()
    scores: dict[str, list[str]] = {}
    for category, keywords in _CATEGORY_KEYWORDS.items():
        matched = [kw for kw in keywords if kw in lowered]
        if matched:
            scores[category] = matched

    if not scores:
        return ClassificationResult(
            category=CATEGORY_UNRECOGNIZED,
            confidence=0.0,
            method="keyword_heuristic",
            reasoning="No known document-type phrases found.",
        )

    best_category, best_matches = max(scores.items(), key=lambda kv: len(kv[1]))

    if len(best_matches) < MIN_CONFIDENT_SCORE:
        return ClassificationResult(
            category=CATEGORY_UNRECOGNIZED,
            confidence=round(min(0.3, 0.1 * len(best_matches)), 3),
            method="keyword_heuristic",
            reasoning=(
                f"Only a weak match on {best_category} "
                f"({best_matches}) — below the confidence floor."
            ),
        )

    # Saturating score: more matches raise confidence, capped short of 1.0
    # because a keyword match is corroborating evidence, not proof — the same
    # posture the rest of this product takes toward statistical evidence.
    confidence = round(min(0.95, 0.5 + 0.1 * len(best_matches)), 3)
    return ClassificationResult(
        category=best_category,
        confidence=confidence,
        method="keyword_heuristic",
        reasoning=f"Matched: {', '.join(best_matches)}.",
    )
