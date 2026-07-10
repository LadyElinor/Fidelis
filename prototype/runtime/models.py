from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


RuntimeDecision = Literal["HALT", "REVIEW", "PROCEED"]
RuntimeDisposition = Literal["PROCEED", "SUSPEND", "CONFIRM_HUMAN"]
RiskState = Literal["GREEN", "AMBER", "RED"]
DecisionIntegrity = Literal["FULL", "PARTIAL", "FAILED"]
LensVerdict = Literal["object", "caution", "clear"]


class ActionInput(BaseModel):
    name: str
    description: str
    category: str


class ContextInput(BaseModel):
    data_contains_personal_information: bool
    claimed_anonymized: bool
    retention_policy_clear: bool
    reversible: Literal["full", "partial", "none"]
    human_approval_present: bool
    deployment_pressure: Literal["low", "medium", "high"]


class ClaimsInput(BaseModel):
    expected_benefit: str
    operator_justification: str


class AuthorityInput(BaseModel):
    requester_role: str
    authorization_basis: str


class CaseInput(BaseModel):
    case_id: str = Field(min_length=1)
    action: ActionInput
    context: ContextInput
    claims: ClaimsInput
    authority: AuthorityInput


class LensResult(BaseModel):
    lens: str
    verdict: LensVerdict
    hazards: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    justification: str = Field(min_length=1)
    minority_report: bool = False


class MeaningAssayResult(BaseModel):
    significance: float = Field(ge=0.0, le=1.0)
    warrant: float = Field(ge=0.0, le=1.0)
    reasoning: list[str] = Field(default_factory=list)
    available: bool = True
    malformed: bool = False


class TelemetryVector(BaseModel):
    agency_level: float = Field(ge=0.0, le=1.0)
    reversibility: float = Field(ge=0.0, le=1.0)
    affected_parties: float = Field(ge=0.0, le=1.0)
    evidence_quality: float = Field(ge=0.0, le=1.0)
    consent_quality: float = Field(ge=0.0, le=1.0)
    independence_score: float = Field(ge=0.0, le=1.0)
    dissent_present: bool
    execution_pressure: float = Field(ge=0.0, le=1.0)
    available: bool = True
    malformed: bool = False


class DissentRecord(BaseModel):
    source: str
    severity: Literal["object", "caution"]
    hazards: list[str] = Field(default_factory=list)
    justification: str = Field(min_length=1)
    resolution_status: Literal["unresolved", "addressed", "overridden"] = "unresolved"
    override_rationale: str | None = None


class DependencyNode(BaseModel):
    node_id: str
    kind: str
    independence_class: Literal["independent", "derived", "unknown"] = "unknown"
    notes: list[str] = Field(default_factory=list)


class DependencyEdge(BaseModel):
    source: str
    target: str
    edge_type: Literal["supports", "objects_to", "derived_from", "gates", "overrides"]
    note: str = ""


class OverrideRecord(BaseModel):
    override_requested: bool = False
    override_source: str | None = None
    rationale: str | None = None
    approved: bool = False


class CoverageRecord(BaseModel):
    layer: str
    mode: Literal["direct-real", "derived-advisory", "missing"]
    notes: list[str] = Field(default_factory=list)


class EvidenceRecord(BaseModel):
    kind: str
    source: str
    independence_class: Literal["independent", "derived", "degraded", "unknown"] = "unknown"
    notes: list[str] = Field(default_factory=list)


class RuntimeDecisionResult(BaseModel):
    case_id: str
    runtime_decision: RuntimeDecision
    runtime_disposition: RuntimeDisposition = "SUSPEND"
    risk_state: RiskState
    decision_integrity: DecisionIntegrity
    reason: str
    unresolved_dissent: list[str] = Field(default_factory=list)
    dissent_records: list[DissentRecord] = Field(default_factory=list)
    independent_evidence_routes: list[str] = Field(default_factory=list)
    co_dependency_flags: list[str] = Field(default_factory=list)
    integrity_rationale: list[str] = Field(default_factory=list)
    route_quality: dict[str, str] = Field(default_factory=dict)
    coverage_records: list[CoverageRecord] = Field(default_factory=list)
    evidence_records: list[EvidenceRecord] = Field(default_factory=list)
    degradation_policy_row: str = ""
    human_escalation_required: bool = False
    override_record: OverrideRecord = Field(default_factory=OverrideRecord)
    receipt_hash: str = ""
    parent_receipts: list[str] = Field(default_factory=list)
