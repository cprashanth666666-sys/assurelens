"""Object storage for uploaded document bytes.

`documents.storage_key`/`storage_backend` are the only trace Postgres keeps of
where the bytes live — the bytes themselves never enter the database. That
mirrors the evidence-hashing precedent elsewhere in this codebase (payloads
are hashed and summarised, never fully stored) and avoids putting binary blobs
in a database that is backed up, restored and queried as if it were all
structured data.

Two implementations behind one `DocumentStorage` interface:

* `LocalFilesystemStorage` — correct for docker-compose, and for a Render
  **paid** plan with a persistent disk attached.
* `S3CompatibleStorage` — for Render's **free** plan, which this project
  actually deploys on (see render.yaml/DEPLOY.md) and which has **no
  persistent-disk option at all**: the container filesystem is wiped on every
  deploy and every scale-to-zero cycle, so `LocalFilesystemStorage` there
  would silently lose every uploaded document on the next push. This mirrors
  why Postgres lives on Neon rather than Render's own free database — same
  constraint, same fix: a small, no-expiry free-tier object store outside the
  ephemeral compute. Cloudflare R2's free tier (10GB, S3-compatible, no
  egress fee) is the natural fit and needs no new client library — the S3
  wire protocol is what `S3CompatibleStorage` speaks.

Which one runs is a config choice (`STORAGE_BACKEND`), not a code choice —
see `get_storage()`.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol


class DocumentStorage(Protocol):
    backend_name: str

    def put(self, key: str, data: bytes) -> None: ...

    def get(self, key: str) -> bytes: ...

    def exists(self, key: str) -> bool: ...


def _validate_key(key: str) -> None:
    # Keys are always a hex hash, optionally with a fixed suffix (see
    # storage_key_for) — reject anything else so a key can never traverse out
    # of the storage root or be used to smuggle a path/object-key injection.
    if not key or not all(c.isalnum() or c in "._-" for c in key):
        raise ValueError(f"unsafe storage key: {key!r}")


class LocalFilesystemStorage:
    """Stores bytes under a root directory, keyed by content hash.

    Correct for docker-compose and for a deployment with real persistent
    storage attached to the container. Wrong for Render's free plan — see the
    module docstring — which is why `get_storage()` does not default to this
    in production.
    """

    backend_name = "local"

    def __init__(self, root: str) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        _validate_key(key)
        # Two-level fan-out so one directory never holds tens of thousands of
        # files, which some filesystems handle badly.
        return self._root / key[:2] / key[2:4] / key

    def put(self, key: str, data: bytes) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Write-then-rename: a reader can never observe a partially written
        # file, which matters once background extraction reads it concurrently
        # with a slow upload elsewhere.
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(data)
        os.replace(tmp, path)

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()


class S3CompatibleStorage:
    """Stores bytes in an S3-compatible bucket (AWS S3, Cloudflare R2, ...).

    Talks plain S3 API via boto3 — R2 exposes an S3-compatible endpoint, so no
    R2-specific client is needed, only its endpoint URL and credentials.
    """

    backend_name = "s3"

    def __init__(
        self, *, bucket: str, endpoint_url: str | None, region: str, access_key: str,
        secret_key: str,
    ) -> None:
        import boto3  # deferred: only this backend needs it

        self._bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url or None,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    def put(self, key: str, data: bytes) -> None:
        _validate_key(key)
        self._client.put_object(Bucket=self._bucket, Key=key, Body=data)

    def get(self, key: str) -> bytes:
        _validate_key(key)
        response = self._client.get_object(Bucket=self._bucket, Key=key)
        return response["Body"].read()  # type: ignore[no-any-return]

    def exists(self, key: str) -> bool:
        _validate_key(key)
        from botocore.exceptions import ClientError

        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in ("404", "NoSuchKey"):
                return False
            raise


_storage: DocumentStorage | None = None


def get_storage() -> DocumentStorage:
    global _storage
    if _storage is None:
        from app.config import get_settings

        settings = get_settings()
        if settings.storage_backend == "s3":
            if not settings.s3_bucket:
                raise RuntimeError(
                    "STORAGE_BACKEND=s3 requires S3_BUCKET (and the other S3_* settings)."
                )
            _storage = S3CompatibleStorage(
                bucket=settings.s3_bucket,
                endpoint_url=settings.s3_endpoint_url or None,
                region=settings.s3_region,
                access_key=settings.s3_access_key_id,
                secret_key=settings.s3_secret_access_key,
            )
        else:
            _storage = LocalFilesystemStorage(settings.document_storage_dir)
    return _storage


def storage_key_for(content_hash: str, suffix: str = "") -> str:
    """The object key for a document's bytes, or `suffix`-decorated derivative
    (e.g. its overflow extracted text)."""
    return f"{content_hash}{suffix}"
