"""Fetches a submitted URL for document intake, safely.

Redirects are followed manually, one hop at a time, with `assert_safe_url`
re-run against each `Location` header — `httpx`'s built-in redirect following
would issue the follow-up request before this module gets a chance to reject
it, which is exactly the gap that turns "check the URL once" into a bypass.
"""

from __future__ import annotations

import httpx

from app.ingest.ssrf import assert_safe_url

MAX_REDIRECTS = 5
FETCH_TIMEOUT = httpx.Timeout(15.0, connect=5.0)


class FetchError(Exception):
    """The URL could not be safely or successfully fetched."""


def fetch_url(url: str, max_bytes: int) -> tuple[bytes, str | None]:
    """Returns (body, content_type). Raises FetchError / UnsafeUrl."""
    assert_safe_url(url)
    current = url

    with httpx.Client(follow_redirects=False, timeout=FETCH_TIMEOUT) as client:
        for _ in range(MAX_REDIRECTS + 1):
            try:
                response = client.get(current)
            except httpx.HTTPError as exc:
                raise FetchError(f"could not reach {current!r}: {exc}") from exc

            if response.is_redirect:
                location = response.headers.get("location")
                if not location:
                    raise FetchError("redirect with no Location header")
                current = str(response.next_request.url) if response.next_request else location
                assert_safe_url(current)
                continue

            if response.status_code >= 400:
                raise FetchError(f"{current!r} returned HTTP {response.status_code}")

            content_length = response.headers.get("content-length")
            if content_length is not None and int(content_length) > max_bytes:
                raise FetchError(
                    f"response is {content_length} bytes, over the {max_bytes} limit"
                )

            body = response.content
            if len(body) > max_bytes:
                raise FetchError(f"response exceeded {max_bytes} bytes")

            return body, response.headers.get("content-type")

    raise FetchError(f"too many redirects (> {MAX_REDIRECTS})")
