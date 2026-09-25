"""Object storage for uploaded document bytes.

`documents.storage_key`/`storage_backend` are the only trace Postgres keeps of
where the bytes live — the bytes themselves never enter the database. That
mirrors the evidence-hashing precedent elsewhere in this codebase (payloads
are hashed and summarised, never fully stored) and avoids putting binary blobs
in a database that is backed up, restored and queried as if it were all
structured data.

`LocalFilesystemStorage` is today's implementation, good enough for the
docker-compose deployment and for Render's persistent disk. `DocumentStorage`
is the seam: swapping in an S3/R2 backend later means writing one class, not
touching any caller.
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


class LocalFilesystemStorage:
    """Stores bytes under a root directory, keyed by content hash.

    The key is always derived from the sha256 of the content (see
    `storage_key_for`), never from a user-supplied filename — a submitted name
    like `../../etc/passwd` never becomes a path component.
    """

    backend_name = "local"

    def __init__(self, root: str) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # Keys are always a hex hash, optionally with a fixed suffix (see
        # storage_key_for) — reject anything else so a key can never traverse
        # out of the storage root.
        if not key or not all(c.isalnum() or c in "._-" for c in key):
            raise ValueError(f"unsafe storage key: {key!r}")
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


_storage: DocumentStorage | None = None


def get_storage() -> DocumentStorage:
    global _storage
    if _storage is None:
        from app.config import get_settings

        _storage = LocalFilesystemStorage(get_settings().document_storage_dir)
    return _storage


def storage_key_for(content_hash: str, suffix: str = "") -> str:
    """The object key for a document's bytes, or `suffix`-decorated derivative
    (e.g. its overflow extracted text)."""
    return f"{content_hash}{suffix}"
