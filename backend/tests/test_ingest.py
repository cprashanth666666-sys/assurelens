"""Unit tests for the ingest package: SSRF guard, sniffing, classification.

No database needed — these exercise pure functions directly, unlike
test_documents_api.py which drives the HTTP surface end to end.
"""

from __future__ import annotations

import pytest

from app.ingest.classify import CATEGORY_UNRECOGNIZED, classify_text
from app.ingest.sniff import sniff_mime
from app.ingest.ssrf import UnsafeUrl, assert_safe_url


class TestSsrfGuard:
    def test_loopback_is_blocked(self) -> None:
        with pytest.raises(UnsafeUrl):
            assert_safe_url("http://127.0.0.1/")

    def test_localhost_hostname_is_blocked(self) -> None:
        with pytest.raises(UnsafeUrl):
            assert_safe_url("http://localhost/")

    def test_cloud_metadata_address_is_blocked(self) -> None:
        with pytest.raises(UnsafeUrl):
            assert_safe_url("http://169.254.169.254/latest/meta-data/")

    def test_private_range_is_blocked(self) -> None:
        with pytest.raises(UnsafeUrl):
            assert_safe_url("http://10.0.0.5/")

    def test_non_http_scheme_is_blocked(self) -> None:
        with pytest.raises(UnsafeUrl):
            assert_safe_url("file:///etc/passwd")

    def test_a_public_looking_host_is_allowed_through_the_scheme_and_dns_check(self) -> None:
        # example.com resolves to a public IANA-reserved documentation
        # address, not a private/loopback one, so this must not raise.
        assert_safe_url("https://example.com/")


class TestSniff:
    def test_pdf_magic_bytes(self) -> None:
        assert sniff_mime(b"%PDF-1.4\n...") == "application/pdf"

    def test_html_doctype(self) -> None:
        assert sniff_mime(b"<!DOCTYPE html><html></html>") == "text/html"

    def test_plain_text_falls_back(self) -> None:
        assert sniff_mime(b"just some plain text") == "text/plain"


class TestClassify:
    def test_privacy_notice_is_recognised(self) -> None:
        result = classify_text(
            "This Privacy Notice describes the personal data we collect "
            "and the purpose of processing for each data principal."
        )
        assert result.category == "PRIVACY_NOTICE"
        assert result.confidence > 0.5

    def test_empty_text_is_unrecognized(self) -> None:
        result = classify_text("")
        assert result.category == CATEGORY_UNRECOGNIZED
        assert result.confidence == 0.0

    def test_irrelevant_text_is_unrecognized_rather_than_guessed(self) -> None:
        result = classify_text("the quick brown fox jumps over the lazy dog")
        assert result.category == CATEGORY_UNRECOGNIZED

    def test_vendor_dpa_is_distinguished_from_consent_form(self) -> None:
        result = classify_text(
            "This Data Processing Agreement governs the sub-processor's "
            "handling of personal data on behalf of the data processor."
        )
        assert result.category == "VENDOR_DPA"
