"""The document intake API.

Covers: upload -> stored, extracted and classified end to end; re-uploading
identical bytes resolves to the same row rather than duplicating; a URL
pointed at a private address is refused before any request is issued.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.main import app
from app.models.control import Engagement

pytestmark = pytest.mark.usefixtures("seeded_db")

client = TestClient(app)

SAMPLE_PRIVACY_NOTICE = b"""
This Privacy Notice describes the personal data we collect from each
data principal and the purpose of processing under the DPDP Act. You may
withdraw consent at any time via the consent manager.
""" * 3  # repeated so more than one keyword phrase is present with margin


@pytest.fixture
def engagement_id(seeded_db: Session) -> int:
    engagement = seeded_db.scalar(select(Engagement).order_by(Engagement.id).limit(1))
    assert engagement is not None
    return engagement.id


def test_uploading_a_plain_text_document_is_extracted_and_classified(
    engagement_id: int,
) -> None:
    response = client.post(
        f"/api/engagements/{engagement_id}/documents",
        files={"file": ("notice.txt", SAMPLE_PRIVACY_NOTICE, "text/plain")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "CLASSIFIED"
    assert body["detected_mime"] == "text/plain"
    assert body["extraction"] is not None
    assert body["extraction"]["extraction_error"] is None
    assert body["classification"] is not None
    assert body["classification"]["category"] == "PRIVACY_NOTICE"
    assert body["classification"]["confidence"] > 0.5


def test_an_empty_upload_is_rejected(engagement_id: int) -> None:
    response = client.post(
        f"/api/engagements/{engagement_id}/documents",
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert response.status_code == 422


def test_reuploading_identical_bytes_resolves_to_the_same_document(
    engagement_id: int,
) -> None:
    first = client.post(
        f"/api/engagements/{engagement_id}/documents",
        files={"file": ("a.txt", b"identical content for dedup test", "text/plain")},
    ).json()
    second = client.post(
        f"/api/engagements/{engagement_id}/documents",
        files={"file": ("b.txt", b"identical content for dedup test", "text/plain")},
    ).json()

    assert first["id"] == second["id"]
    assert first["content_hash"] == second["content_hash"]


def test_a_document_unrecognised_by_the_classifier_says_so_rather_than_guessing(
    engagement_id: int,
) -> None:
    response = client.post(
        f"/api/engagements/{engagement_id}/documents",
        files={"file": ("random.txt", b"the quick brown fox jumps", "text/plain")},
    )

    body = response.json()
    assert body["classification"]["category"] == "UNRECOGNIZED"


def test_uploaded_document_appears_in_the_engagement_list(engagement_id: int) -> None:
    uploaded = client.post(
        f"/api/engagements/{engagement_id}/documents",
        files={"file": ("listed.txt", b"content for the listing test case", "text/plain")},
    ).json()

    listing = client.get(f"/api/engagements/{engagement_id}/documents").json()
    assert any(d["id"] == uploaded["id"] for d in listing)


def test_a_url_resolving_to_a_private_address_is_refused(engagement_id: int) -> None:
    response = client.post(
        f"/api/engagements/{engagement_id}/documents/from-url",
        json={"url": "http://127.0.0.1:8000/api/health"},
    )
    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"]


def test_a_url_with_a_disallowed_scheme_is_refused(engagement_id: int) -> None:
    response = client.post(
        f"/api/engagements/{engagement_id}/documents/from-url",
        json={"url": "file:///etc/passwd"},
    )
    assert response.status_code == 400


def test_unknown_engagement_returns_404(engagement_id: int) -> None:
    response = client.post(
        "/api/engagements/999999/documents",
        files={"file": ("x.txt", b"content", "text/plain")},
    )
    assert response.status_code == 404
