"""Response models for the control library API."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict


class ClauseRef(BaseModel):
    """A clause a control cites, with the provenance of that citation."""

    model_config = ConfigDict(from_attributes=True)

    framework_code: str
    framework_name: str
    ref: str
    title: str
    verbatim_text: str | None
    in_force_from: dt.date | None
    source_status: str
    source_note: str | None
    is_primary: bool
    rationale: str | None


class ControlSummary(BaseModel):
    """Row in the control library table."""

    model_config = ConfigDict(from_attributes=True)

    ref: str
    title: str
    domain: str
    inference_mode: str
    is_executable: bool
    suite: str | None
    primary_clause: str | None
    primary_framework: str | None
    framework_refs: list[str]
    in_scope: bool
    na_reason: str | None
    evidence_owner: str | None
    # True when the PRIMARY clause is unverified, which is what
    # G7_SOURCE_UNVERIFIED acts on. An unverified ISO cross-reference does not
    # set this: secondary citations never carry a verdict.
    primary_source_unverified: bool


class ControlDetail(ControlSummary):
    objective: str
    procedure_text: str
    auto_raise: bool
    threshold_overrides: dict[str, object]
    yaml_source: str
    plugin_key: str | None
    evidence_contract: dict[str, object] | None
    clauses: list[ClauseRef]


class EngagementSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    scope_note: str | None
    compliance_deadline: dt.date | None
    organization: str
    city: str | None
    sector: str | None
    headcount: int | None
    is_significant_data_fiduciary: bool
    is_synthetic: bool
    control_count: int
    executable_count: int
    out_of_scope_count: int
