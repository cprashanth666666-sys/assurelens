"""Document intake: file upload and website submission.

Every control this product runs needs evidence; this is where evidence that
isn't a database row or an HTTP probe — a policy PDF, a signed DPA, a
published notice — enters the system. See docs on migration 0006 and
app/ingest/ for why bytes never touch Postgres and why a website URL is
resolved and range-checked before it is ever fetched.

Processing (extraction, classification) happens after the response, via
FastAPI's BackgroundTasks — matching this product's existing preference for
the simplest mechanism that fits the actual latency (runs.py runs suites
synchronously because they fit a budget; this doesn't, because PDF extraction
and a website fetch can each take longer than a request should stay open).
"""

from __future__ import annotations

import datetime as dt
import hashlib

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.config import Settings, get_settings
from app.db import get_db
from app.ingest.fetch import FetchError, fetch_url
from app.ingest.pipeline import process_document
from app.ingest.sniff import sniff_mime
from app.ingest.ssrf import UnsafeUrl
from app.ingest.storage import get_storage, storage_key_for
from app.models.control import Engagement
from app.models.documents import Document

router = APIRouter()


class ClassificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: str
    confidence: float
    method: str
    reasoning: str | None
    classified_at: dt.datetime


class ExtractionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page_count: int | None
    extraction_engine: str
    truncated: bool
    extraction_error: str | None
    # A preview, not the full text — the document list is not a text viewer,
    # and there's no reason to ship potentially large bodies to every list
    # render.
    text_preview: str | None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_type: str
    original_name: str
    detected_mime: str | None
    size_bytes: int
    content_hash: str
    status: str
    rejection_reason: str | None
    created_at: dt.datetime
    processed_at: dt.datetime | None
    extraction: ExtractionOut | None
    classification: ClassificationOut | None


class UrlSubmission(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


def _to_out(document: Document) -> DocumentOut:
    extraction = document.extraction
    classification = document.latest_classification
    return DocumentOut(
        id=document.id,
        source_type=document.source_type,
        original_name=document.original_name,
        detected_mime=document.detected_mime,
        size_bytes=document.size_bytes,
        content_hash=document.content_hash,
        status=document.status,
        rejection_reason=document.rejection_reason,
        created_at=document.created_at,
        processed_at=document.processed_at,
        extraction=(
            None
            if extraction is None
            else ExtractionOut(
                page_count=extraction.page_count,
                extraction_engine=extraction.extraction_engine,
                truncated=extraction.truncated,
                extraction_error=extraction.extraction_error,
                text_preview=(
                    None
                    if extraction.extracted_text is None
                    else extraction.extracted_text[:500]
                ),
            )
        ),
        classification=(
            None
            if classification is None
            else ClassificationOut.model_validate(classification)
        ),
    )


def _store_and_create(
    db: Session,
    *,
    engagement_id: int,
    source_type: str,
    original_name: str,
    data: bytes,
    declared_mime: str | None,
) -> Document:
    content_hash = hashlib.sha256(data).hexdigest()
    detected_mime = sniff_mime(data)
    storage_key = storage_key_for(content_hash)

    if not get_storage().exists(storage_key):
        get_storage().put(storage_key, data)

    document = Document(
        engagement_id=engagement_id,
        source_type=source_type,
        original_name=original_name,
        declared_mime=declared_mime,
        detected_mime=detected_mime,
        size_bytes=len(data),
        content_hash=content_hash,
        storage_backend=get_storage().backend_name,
        storage_key=storage_key,
        status="RECEIVED",
    )
    db.add(document)
    try:
        db.flush()
    except IntegrityError:
        # Same bytes already submitted for this engagement. Re-uploading is
        # not an error — return the existing row rather than a duplicate.
        db.rollback()
        existing = db.scalar(
            select(Document).where(
                Document.engagement_id == engagement_id,
                Document.content_hash == content_hash,
            )
        )
        assert existing is not None  # the constraint that just fired guarantees this
        return existing
    return document


@router.post(
    "/engagements/{engagement_id}/documents",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    engagement_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> DocumentOut:
    engagement = db.get(Engagement, engagement_id)
    if engagement is None:
        raise HTTPException(status_code=404, detail=f"No engagement {engagement_id}")

    data = await file.read(settings.document_max_size_bytes + 1)
    if len(data) > settings.document_max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {settings.document_max_size_bytes} byte limit.",
        )
    if len(data) == 0:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    document = _store_and_create(
        db,
        engagement_id=engagement_id,
        source_type="UPLOAD",
        original_name=file.filename or "unnamed",
        data=data,
        declared_mime=file.content_type,
    )
    db.commit()
    db.refresh(document)

    if document.status == "RECEIVED":
        background_tasks.add_task(process_document, document.id)

    return _to_out(document)


@router.post(
    "/engagements/{engagement_id}/documents/from-url",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
)
def submit_document_url(
    engagement_id: int,
    submission: UrlSubmission,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> DocumentOut:
    engagement = db.get(Engagement, engagement_id)
    if engagement is None:
        raise HTTPException(status_code=404, detail=f"No engagement {engagement_id}")

    try:
        data, content_type = fetch_url(submission.url, settings.document_max_size_bytes)
    except UnsafeUrl as exc:
        # 400, not 500: the request is well-formed, its target is refused.
        raise HTTPException(status_code=400, detail=f"URL not allowed: {exc}") from exc
    except FetchError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if len(data) == 0:
        raise HTTPException(status_code=422, detail="URL returned an empty response.")

    document = _store_and_create(
        db,
        engagement_id=engagement_id,
        source_type="URL",
        original_name=submission.url,
        data=data,
        declared_mime=content_type,
    )
    db.commit()
    db.refresh(document)

    if document.status == "RECEIVED":
        background_tasks.add_task(process_document, document.id)

    return _to_out(document)


@router.get("/engagements/{engagement_id}/documents", response_model=list[DocumentOut])
def list_documents(engagement_id: int, db: Session = Depends(get_db)) -> list[DocumentOut]:
    documents = db.scalars(
        select(Document)
        .where(Document.engagement_id == engagement_id)
        .options(
            selectinload(Document.extraction),
            selectinload(Document.classifications),
        )
        .order_by(Document.created_at.desc())
    ).all()
    return [_to_out(d) for d in documents]


@router.get("/documents/{document_id}", response_model=DocumentOut)
def get_document(document_id: int, db: Session = Depends(get_db)) -> DocumentOut:
    document = db.scalar(
        select(Document)
        .where(Document.id == document_id)
        .options(
            selectinload(Document.extraction),
            selectinload(Document.classifications),
        )
    )
    if document is None:
        raise HTTPException(status_code=404, detail=f"No document {document_id}")
    return _to_out(document)
