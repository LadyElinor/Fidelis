from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from .enums import AdapterProvenance, DecisionIntegrity, NormativeSummary, ReceiptSchemaVersion, RiskState, RuntimeDisposition


class ReceiptRef(BaseModel):
    """A nested receipt reference for provenance, versioning, and future URI support."""

    sha256: str
    schema_version: ReceiptSchemaVersion = ReceiptSchemaVersion.V1_0_0
    path: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProposedAction(BaseModel):
    """Input contract for the full orchestration pipeline."""

    id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    description: str
    context: dict[str, Any] = Field(default_factory=dict)
    proposed_by: str = "agent"


class CouncilAssessment(BaseModel):
    """Prospective hazard review.

    This is not a warrant judgment. It maps hazards, fault lines, irreversibility,
    and suspension triggers under uncertainty before execution.
    """

    decision_id: str
    hazards: list[str] = Field(default_factory=list)
    convergences: list[str] = Field(default_factory=list)
    fault_lines: list[str] = Field(default_factory=list)
    suspension_triggers: list[str] = Field(default_factory=list)
    minority_reports: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    confidence_notes: list[str] = Field(default_factory=list)
    irreversibility_score: float = Field(ge=0.0, le=1.0, default=0.0)
    contested: bool = False
    raw_lens_outputs: dict[str, Any] = Field(default_factory=dict)
    adapter_provenance: AdapterProvenance = AdapterProvenance.UNAVAILABLE
    receipt: ReceiptRef


class WarrantAssay(BaseModel):
    """Normative interpretation sidecar.

    This is not the runtime branch decision. It records significance, warrant,
    quadrant-style summary, failure modes, and pair-contrast context where available.
    """

    decision_id: str
    significance: float = Field(ge=0.0, le=1.0, default=0.0)
    warrant: float | None = Field(default=None, ge=-1.0, le=1.0)
    normative_summary: NormativeSummary = NormativeSummary.UNDETERMINED
    failure_modes: list[str] = Field(default_factory=list)
    pair_contrasts: dict[str, Any] | None = None
    confidence_notes: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    contested: bool = False
    adapter_provenance: AdapterProvenance = AdapterProvenance.UNAVAILABLE
    receipt: ReceiptRef


class CERRecordBundle(BaseModel):
    """Evidence-spine output.

    The internal vector and invariant schemas remain intentionally provisional here;
    they should be narrowed once the real CER/SOPHRON adapters are wired.
    """

    execution_id: str
    state_vectors: list[dict[str, Any]] = Field(default_factory=list)
    invariants_checked: list[dict[str, Any]] = Field(default_factory=list)
    provenance_hashes: list[str] = Field(default_factory=list)
    sophron_validation: dict[str, Any] = Field(default_factory=dict)
    confidence_notes: list[str] = Field(default_factory=list)
    adapter_provenance: AdapterProvenance = AdapterProvenance.UNAVAILABLE
    receipt: ReceiptRef


class ReconciliationRecord(BaseModel):
    case_key: str | None = None
    council_verdict: str
    warranted_action: str
    alignment: str
    rationale: str
    receipt: ReceiptRef | None = None


class ExecutionDecision(BaseModel):
    """Unified output contract.

    Runtime disposition remains separate from normative interpretation so the system
    can distinguish what it did from what kind of act it judged the proposal to be.
    """

    action_id: str
    council: CouncilAssessment
    warrant: WarrantAssay | None = None
    cer_bundle: CERRecordBundle
    vita_state: dict[str, Any] = Field(default_factory=dict)
    risk_state: RiskState = RiskState.AMBER
    runtime_disposition: RuntimeDisposition = RuntimeDisposition.SUSPEND
    normative_summary: NormativeSummary = NormativeSummary.UNDETERMINED
    confidence_notes: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    contested: bool = False
    decision_integrity: DecisionIntegrity = DecisionIntegrity.DEMO_ONLY
    adapter_provenance: dict[str, AdapterProvenance] = Field(default_factory=dict)
    process_provenance: dict[str, dict[str, Any]] = Field(default_factory=dict)
    reconciliation: ReconciliationRecord | None = None
    hazard_profile: dict[str, Any] = Field(default_factory=dict)
    overall_receipt: ReceiptRef
