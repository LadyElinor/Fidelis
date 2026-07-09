from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


RuntimeDecision = Literal["HALT", "REVIEW", "PROCEED"]
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


class TelemetryVector(BaseModel):
    agency_level: float = Field(ge=0.0, le=1.0)
    reversibility: float = Field(ge=0.0, le=1.0)
    affected_parties: float = Field(ge=0.0, le=1.0)
    evidence_quality: float = Field(ge=0.0, le=1.0)
    consent_quality: float = Field(ge=0.0, le=1.0)
    independence_score: float = Field(ge=0.0, le=1.0)
    dissent_present: bool
    execution_pressure: float = Field(ge=0.0, le=1.0)


class RuntimeDecisionResult(BaseModel):
    case_id: str
    runtime_decision: RuntimeDecision
    risk_state: RiskState
    decision_integrity: DecisionIntegrity
    reason: str
    unresolved_dissent: list[str] = Field(default_factory=list)
    receipt_hash: str = ""
    parent_receipts: list[str] = Field(default_factory=list)
