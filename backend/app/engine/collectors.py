"""The default evidence broker.

Suites register how to obtain the evidence they declared. Until one does, a
name resolves to nothing and the control gates on G4_MISSING_ARTIFACT.

That is the honest behaviour, not a gap. A broker that invented plausible
data so a control could return PASS would be the exact failure this product
exists to refuse -- and it would do it silently, which is worse.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import httpx

from app.config import get_settings
from app.engine.evidence import EvidenceBroker, EvidenceKind, TargetUnreachable

log = logging.getLogger(__name__)

# Evidence name -> callable(context) -> payload. Suites populate this at
# import time via `register_query`.
_DB_QUERIES: dict[str, Callable[[dict[str, Any]], Any]] = {}

# Evidence name -> callable(context, client) -> payload.
_HTTP_PROBES: dict[str, Callable[[dict[str, Any], httpx.Client], Any]] = {}


def register_query(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Register how to obtain a named piece of database evidence."""

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        if name in _DB_QUERIES:
            raise ValueError(f"evidence query {name!r} is already registered")
        _DB_QUERIES[name] = fn
        return fn

    return decorator


def register_probe(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Register how to obtain a named piece of probe evidence."""

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        if name in _HTTP_PROBES:
            raise ValueError(f"evidence probe {name!r} is already registered")
        _HTTP_PROBES[name] = fn
        return fn

    return decorator


def registered_evidence() -> dict[str, list[str]]:
    return {"db_queries": sorted(_DB_QUERIES), "http_probes": sorted(_HTTP_PROBES)}


def _collect_db(name: str, context: dict[str, Any]) -> Any:
    query = _DB_QUERIES.get(name)
    if query is None:
        # Not an error: no suite has said how to obtain this yet. Returning
        # None makes the gate report it as missing evidence, which is true.
        log.debug("no registered query for evidence %r", name)
        return None
    return query(context)


def _collect_probe(name: str, context: dict[str, Any]) -> Any:
    probe = _HTTP_PROBES.get(name)
    if probe is None:
        return None

    settings = get_settings()
    try:
        with httpx.Client(
            base_url=settings.target_service_url,
            timeout=httpx.Timeout(10.0, connect=5.0),
        ) as client:
            return probe(context, client)
    except httpx.HTTPError as exc:
        # Distinct from absent. The evidence exists; the system holding it
        # could not be reached, and the gate reports that as G8 rather than
        # G4 because the remedy is different.
        raise TargetUnreachable(str(exc)) from exc


def _collect_attestation(name: str, context: dict[str, Any]) -> Any:
    """Attestations are supplied with the engagement, not gathered.

    Nothing returns one yet, and that is deliberate: an attestation can never
    carry a verdict on its own, so a control resting only on one must gate.
    """
    return None


def _collect_file(name: str, context: dict[str, Any]) -> Any:
    return None


def default_broker() -> EvidenceBroker:
    broker = EvidenceBroker()
    broker.register(EvidenceKind.DB_QUERY, _collect_db)
    broker.register(EvidenceKind.HTTP_PROBE, _collect_probe)
    broker.register(EvidenceKind.ATTESTATION, _collect_attestation)
    broker.register(EvidenceKind.FILE_ARTIFACT, _collect_file)
    return broker
