"""Unit tests for the ingest package: SSRF guard, sniffing, classification.

No database needed — these exercise pure functions directly, unlike
test_documents_api.py which drives the HTTP surface end to end.
"""

from __future__ import annotations

import pytest

from app.ingest.classify import CATEGORY_UNRECOGNIZED, classify_text
from app.ingest.extract import extract_text
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


def _minimal_pdf(text: str) -> bytes:
    """A valid one-page PDF with a text stream, built by hand so the test
    needs no PDF-writing dependency. xref offsets are computed, not guessed."""
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream
        + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref}\n%%EOF\n"
    ).encode()
    return bytes(out)


class TestExtractEachFormat:
    """Every format the intake page advertises, through sniff -> extract."""

    def test_pdf(self) -> None:
        data = _minimal_pdf("Data Processing Agreement with sub-processor")
        assert sniff_mime(data) == "application/pdf"
        result = extract_text(data)
        assert result.error is None
        assert result.page_count == 1
        assert "Data Processing Agreement" in (result.text or "")

    def test_docx(self) -> None:
        import io

        from docx import Document

        doc = Document()
        doc.add_paragraph("Grievance Redressal procedure")
        buf = io.BytesIO()
        doc.save(buf)
        data = buf.getvalue()

        assert sniff_mime(data) == (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        result = extract_text(data)
        assert result.error is None
        assert "Grievance Redressal" in (result.text or "")

    def test_xlsx(self) -> None:
        import io

        from openpyxl import Workbook

        wb = Workbook()
        wb.active.append(["Retention schedule", "7 years"])  # type: ignore[union-attr]
        buf = io.BytesIO()
        wb.save(buf)
        data = buf.getvalue()

        assert sniff_mime(data) == (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        result = extract_text(data)
        assert result.error is None
        assert "Retention schedule | 7 years" in (result.text or "")

    def test_html_drops_script_content(self) -> None:
        data = b"<html><body><h1>Privacy Policy</h1><script>evil()</script></body></html>"
        result = extract_text(data)
        assert result.error is None
        assert "Privacy Policy" in (result.text or "")
        assert "evil" not in (result.text or "")

    def test_a_corrupt_pdf_is_a_recorded_failure_not_a_crash(self) -> None:
        result = extract_text(b"%PDF-1.4\nthis is not a real pdf")
        assert result.text is None
        assert result.error is not None


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
