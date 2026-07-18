from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

from .provenance import AdapterProvenance, ReceiptRef, SourceIdentity


class ClaimLevel(StrEnum):
    OBSERVATION = "observation"
    EXPERIENCE = "experience"
    INTERPRETATION = "interpretation"
    SYMBOLIC_ASSOCIATION = "symbolic_association"
    CAUSAL_CLAIM = "causal_claim"
    IDENTITY_ATTRIBUTION = "identity_attribution"
    ACTION_RECOMMENDATION = "action_recommendation"
    COMMITMENT = "commitment"


class CandidateStatus(StrEnum):
    GENERATED = "generated"
    QUALIFYING = "qualifying"
    PRIVATE_USE = "private_use"
    REVERSIBLE_PILOT = "reversible_pilot"
    DEFERRED_RETURN = "deferred_return"
    QUALIFIED = "qualified"
    REJECTED = "rejected"


class ConstraintType(StrEnum):
    DEAD = "dead"
    ENABLING = "enabling"
    EXTRACTIVE = "extractive"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class BlastRadius(StrEnum):
    PRIVATE = "private"
    LOCAL = "local"
    SHARED = "shared"
    INSTITUTIONAL = "institutional"
    PUBLIC = "public"


class ReturnStatus(StrEnum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    PARTIAL = "partial"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class PromotionRecord:
    source_level: ClaimLevel
    target_level: ClaimLevel
    statement: str
    evidence_refs: tuple[str, ...] = ()
    warranted: bool | None = None
    confidence: float | None = None
    reason: str = ""

    def __post_init__(self) -> None:
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class ConstraintAssessment:
    constraint: str
    constraint_type: ConstraintType
    beneficiaries: tuple[str, ...] = ()
    burden_bearers: tuple[str, ...] = ()
    capacities_enabled: tuple[str, ...] = ()
    capacities_suppressed: tuple[str, ...] = ()
    exit_available: bool | None = None
    revision_available: bool | None = None
    rationale: str = ""


@dataclass(frozen=True, slots=True)
class ExposureProfile:
    affected_parties: tuple[str, ...] = ()
    self_regarding: bool = False
    voluntary_for_all: bool | None = None
    reversible: bool = False
    domains: tuple[str, ...] = ()
    authority_scope: str = "unspecified"
    blast_radius: BlastRadius = BlastRadius.PRIVATE


@dataclass(frozen=True, slots=True)
class ProjectionAssessment:
    detected: bool = False
    subject: str | None = None
    assigned_identity: str | None = None
    interpreter_owned_language_available: bool = True
    autonomy_risk: float = 0.0
    rationale: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.autonomy_risk <= 1.0:
            raise ValueError("autonomy_risk must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class ReturnAssessment:
    altered_or_high_arousal_origin: bool | None = None
    elapsed_time_seconds: int | None = None
    ordinary_state_recheck: bool = False
    independent_review_completed: bool = False
    survives_counterevidence: bool | None = None
    revision_tolerated: bool | None = None
    daily_practice_evidence: tuple[str, ...] = ()
    status: ReturnStatus = ReturnStatus.NOT_REQUIRED

    def __post_init__(self) -> None:
        if self.elapsed_time_seconds is not None and self.elapsed_time_seconds < 0:
            raise ValueError("elapsed_time_seconds cannot be negative")


@dataclass(frozen=True, slots=True)
class BelarionAssay:
    decision_id: str
    candidate_status: CandidateStatus
    promotions: tuple[PromotionRecord, ...]
    constraint_assessments: tuple[ConstraintAssessment, ...]
    exposure: ExposureProfile
    projection: ProjectionAssessment
    return_assessment: ReturnAssessment
    significance_warrant_separated: bool
    private_meaning_promoted_to_public_authority: bool
    recommended_gate: str
    failure_modes: tuple[str, ...] = ()
    unresolved_questions: tuple[str, ...] = ()
    confidence_notes: tuple[str, ...] = ()
    contested: bool = False
    provenance: AdapterProvenance = AdapterProvenance.UNAVAILABLE
    source: SourceIdentity | None = None
    receipt: ReceiptRef | None = None
    schema_version: str = field(default="belarion-0.1", init=False)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
