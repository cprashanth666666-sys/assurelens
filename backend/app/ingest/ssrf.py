"""Guards against a website-URL intake becoming a request forwarder into
internal infrastructure.

An intake portal that fetches whatever URL a user submits is, by default, a
way to make this server issue requests to *itself* and its neighbours: the
cloud metadata endpoint, the target_service, the database's network segment.
Every hostname is resolved and every resolved address is checked before any
request is sent, and redirects are re-checked on each hop — the initial host
can be public while a redirect points inward.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"http", "https"}


class UnsafeUrl(ValueError):
    """The URL, or something it resolves/redirects to, is not fetchable."""


def _is_blocked_address(addr: str) -> bool:
    ip = ipaddress.ip_address(addr)
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
        # Cloud metadata endpoints (AWS/GCP/Azure all use this address).
        or str(ip) == "169.254.169.254"
    )


def assert_safe_url(url: str) -> None:
    """Raises UnsafeUrl if the URL must not be fetched.

    Call this on the original URL and again on the `Location` of every
    redirect actually followed — a check performed once, before the first
    request, does not cover a server that responds 200 to the check and then
    302s the real fetch somewhere else.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise UnsafeUrl(f"unsupported scheme: {parsed.scheme!r}")
    if not parsed.hostname:
        raise UnsafeUrl("URL has no host")

    try:
        resolved = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror as exc:
        raise UnsafeUrl(f"could not resolve host: {parsed.hostname!r}") from exc

    for _family, _, _, _, sockaddr in resolved:
        addr = str(sockaddr[0])
        if _is_blocked_address(addr):
            raise UnsafeUrl(
                f"{parsed.hostname!r} resolves to a non-routable address ({addr})"
            )
