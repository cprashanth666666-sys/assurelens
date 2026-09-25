"""Background processing: bytes in storage -> extracted text -> classification.

Runs after the HTTP response for the upload/URL-submission request has
already returned (see api/documents.py), so this owns its own DB session
rather than reusing the request-scoped one, which FastAPI closes as soon as
the endpoint returns.
"""

from __future__ import annotations

import datetime as dt
import logging

from app.config import get_settings
from app.db import get_session_factory
from app.ingest.classify import classify_text
from app.ingest.extract import extract_text
from app.ingest.storage import get_storage, storage_key_for
from app.models.documents import Document, DocumentClassification, DocumentExtraction

log = logging.getLogger(__name__)


def process_document(document_id: int) -> None:
    settings = get_settings()
    session = get_session_factory()()
    try:
        document = session.get(Document, document_id)
        if document is None:
            log.warning("process_document: document %s no longer exists", document_id)
            return

        document.status = "PROCESSING"
        session.commit()

        raw = get_storage().get(document.storage_key)
        result = extract_text(raw, document.detected_mime)

        text = result.text
        truncated = False
        text_storage_key = None
        if text is not None and len(text) > settings.document_max_inline_text_chars:
            truncated = True
            text_storage_key = storage_key_for(document.content_hash, suffix=".text")
            get_storage().put(text_storage_key, text.encode("utf-8"))
            text = text[: settings.document_max_inline_text_chars]

        session.add(
            DocumentExtraction(
                document_id=document.id,
                extracted_text=text,
                text_storage_key=text_storage_key,
                truncated=truncated,
                page_count=result.page_count,
                extraction_engine=result.engine,
                extraction_error=result.error,
            )
        )

        if result.error is not None:
            document.status = "FAILED"
            document.rejection_reason = f"extraction failed: {result.error}"
            document.processed_at = dt.datetime.now(dt.UTC)
            session.commit()
            return

        document.status = "EXTRACTED"
        session.commit()

        classification = classify_text(text)
        session.add(
            DocumentClassification(
                document_id=document.id,
                category=classification.category,
                confidence=classification.confidence,
                method=classification.method,
                reasoning=classification.reasoning,
            )
        )
        document.status = "CLASSIFIED"
        document.processed_at = dt.datetime.now(dt.UTC)
        session.commit()
    except Exception:
        log.exception("process_document failed for document %s", document_id)
        session.rollback()
        document = session.get(Document, document_id)
        if document is not None:
            document.status = "FAILED"
            document.rejection_reason = "internal error during processing"
            document.processed_at = dt.datetime.now(dt.UTC)
            session.commit()
    finally:
        session.close()
