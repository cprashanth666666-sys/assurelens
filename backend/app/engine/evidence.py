"""Evidence collection.

A procedure declares what it needs before it runs. The broker gathers it, and
whatever is missing becomes a gate reason rather than a silent absence -- a
control that could not obtain its evidence must not be reported as a control
that passed.

Everything collected is hashed, so the workpaper can assert the evidence has
not changed since the conclusion was drawn from it.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class EvidenceKind(StrEnum):
    DB_QUERY = "DB_QUERY"
    HTTP_PROBE = "HTTP_PROBE"
    FILE_ARTIFACT = "FILE_ARTIFACT"
    # Someone confirming the control exists. Evidence ABOUT a control, never
    # evidence that it operated -- see `EvidenceBundle.is_attestation_only`.
    ATTESTATION = "ATTESTATION"


@dataclass(frozen=True)
class EvidenceItem:
    name: str
    kind: EvidenceKind
    source_ref: str
    payload: Any
    collected_at: dt.datetime
    content_hash: str

    @property
    def age_days(self) -> int:
        return (dt.datetime.now(dt.UTC) - self.collected_at).days


@dataclass(frozen=True)
class EvidenceRequirement:
    name: str
    kind: EvidenceKind
    # The item whose row count defines the population this control infers
    # about. Without it there is no coverage to compute.
    defines_population: bool = False


@dataclass(frozen=True)
class EvidenceContract:
    """What a procedure must obtain before it is entitled to a verdict."""

    required: tuple[EvidenceRequirement, ...] = ()
    max_age_days: int | None = None


@dataclass
class EvidenceBundle:
    items: dict[str, EvidenceItem] = field(default_factory=dict)
    missing: tuple[str, ...] = ()
    unreachable: bool = False

    def __getitem__(self, name: str) -> EvidenceItem:
        return self.items[name]

    def payload(self, name: str, default: Any = None) -> Any:
        item = self.items.get(name)
        return default if item is None else item.payload

    @property
    def is_attestation_only(self) -> bool:
        """True when nothing was obtained but someone's word.

        This is the failure mode of every questionnaire-based compliance
        tool: a confirmation that a control exists, counted as proof that it
        operated. The two are not the same, and treating them as such is how
        an untested estate ends up green.
        """
        if not self.items:
            return False
        return all(i.kind is EvidenceKind.ATTESTATION for i in self.items.values())

    @property
    def newest_age_days(self) -> int | None:
        if not self.items:
            return None
        return min(i.age_days for i in self.items.values())


def content_hash(payload: Any) -> str:
    """SHA-256 of a canonical rendering.

    Sorted keys and a fixed separator, so the same evidence hashes the same
    regardless of dict ordering -- otherwise the workpaper's integrity claim
    would break on a Python version change rather than on tampering.
    """
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), default=str
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class EvidenceBroker:
    """Resolves an evidence contract into a bundle.

    Collectors are registered by kind, which keeps the engine independent of
    where evidence comes from: a suite that reads the database and one that
    probes a service over HTTP use the same machinery.
    """

    def __init__(self) -> None:
        self._collectors: dict[EvidenceKind, Any] = {}

    def register(self, kind: EvidenceKind, collector: Any) -> None:
        self._collectors[kind] = collector

    def collect(
        self, contract: EvidenceContract, context: dict[str, Any]
    ) -> EvidenceBundle:
        bundle = EvidenceBundle()
        missing: list[str] = []

        for requirement in contract.required:
            collector = self._collectors.get(requirement.kind)
            if collector is None:
                missing.append(requirement.name)
                continue

            try:
                payload = collector(requirement.name, context)
            except TargetUnreachable:
                # Distinct from "absent": the evidence exists, the system
                # holding it could not be reached. Different remedy, and the
                # gate reports it as G8 rather than G4.
                bundle.unreachable = True
                missing.append(requirement.name)
                continue
            except Exception:  # noqa: BLE001 - a failed collector is missing evidence
                missing.append(requirement.name)
                continue

            if payload is None:
                missing.append(requirement.name)
                continue

            bundle.items[requirement.name] = EvidenceItem(
                name=requirement.name,
                kind=requirement.kind,
                source_ref=str(context.get("source_ref", requirement.name)),
                payload=payload,
                collected_at=dt.datetime.now(dt.UTC),
                content_hash=content_hash(payload),
            )

        bundle.missing = tuple(missing)
        return bundle


class TargetUnreachable(Exception):
    """The system under test could not be reached.

    Raised rather than returned so a collector cannot accidentally report an
    unreachable target as an empty result -- which would let a probe suite
    pass by testing nothing.
    """
