"""Both DocumentStorage backends, tested against the real thing.

`moto` runs a real in-memory S3 API server, so S3CompatibleStorage is
exercised through actual boto3 request/response handling rather than a
hand-rolled mock — the same preference this project applies to Postgres over
sqlite elsewhere in the suite.
"""

from __future__ import annotations

import pytest
from moto import mock_aws

from app.ingest.storage import LocalFilesystemStorage, S3CompatibleStorage


class TestLocalFilesystemStorage:
    def test_put_then_get_roundtrips(self, tmp_path: object) -> None:
        storage = LocalFilesystemStorage(str(tmp_path))
        storage.put("abc123", b"hello world")
        assert storage.get("abc123") == b"hello world"

    def test_exists_is_false_before_put(self, tmp_path: object) -> None:
        storage = LocalFilesystemStorage(str(tmp_path))
        assert storage.exists("neverwritten") is False

    def test_a_key_that_would_traverse_out_of_root_is_rejected(
        self, tmp_path: object
    ) -> None:
        storage = LocalFilesystemStorage(str(tmp_path))
        with pytest.raises(ValueError):
            storage.put("../../etc/passwd", b"malicious")


@mock_aws
class TestS3CompatibleStorage:
    def _storage(self) -> S3CompatibleStorage:
        import boto3

        boto3.client("s3", region_name="us-east-1").create_bucket(Bucket="test-bucket")
        return S3CompatibleStorage(
            bucket="test-bucket",
            endpoint_url=None,
            region="us-east-1",
            access_key="fake",
            secret_key="fake",
        )

    def test_put_then_get_roundtrips(self) -> None:
        storage = self._storage()
        storage.put("abc123", b"hello world")
        assert storage.get("abc123") == b"hello world"

    def test_exists_is_false_before_put(self) -> None:
        storage = self._storage()
        assert storage.exists("neverwritten") is False

    def test_exists_is_true_after_put(self) -> None:
        storage = self._storage()
        storage.put("abc123", b"data")
        assert storage.exists("abc123") is True

    def test_an_unsafe_key_is_rejected_before_any_request(self) -> None:
        storage = self._storage()
        with pytest.raises(ValueError):
            storage.put("../escape", b"malicious")
