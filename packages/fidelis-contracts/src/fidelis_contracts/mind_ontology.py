from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

from .provenance import AdapterProvenance, ReceiptRef, SourceIdentity


class MindOntologyProbeMode(StrEnum):
    BEHAVIORAL_BLACK_BOX = "behavioral_black_box"
    REPRESENTATIONAL_WHITE_BOX = "representational_white_box"
    INTERVENTIONAL_WHITE_BOX = "interventional_white_box"


class MindOntologyInterpretation(StrEnum):
    REFERENCE_PATTERN_OBSERVED = "reference_pattern_observed"
    REFERENCE_PATTERN_NOT_OBSERVED = "reference_pattern_not_observed"
    INCONCLUSIVE = "inconclusive"
    UNSUPPORTED = "unsupported"
    NOT_APPLICABLE = "not_applicable"


class MindOntologyCausalSupport(StrEnum):
    OBSERVATIONAL_ONLY = "observational_only"
    COMPARATIVE = "comparative"
    INTERVENTIONAL = "interventional"
    INDEPENDENTLY_REPLICATED = "independently_replicated"


@dataclass(frozen=True, slots=True)
class MetricObservation:
    metric: str
    value: float
    units: str | None = None
    baseline_value: float | None = None
    delta_value: float | None = None
    sign_convention: str | None = None
    reference_population_id: str | None = None
    reference_dataset_revision: str | None = None
    rationale: str = ""


@dataclass(frozen=True, slots=True)
class BehavioralObservation:
    prompt_set_digest: str
    decoding_config_digest: str
    system_prompt_digest: str | None = None
    summary: str = ""
    metrics: tuple[MetricObservation, ...] = ()


@dataclass(frozen=True, slots=True)
class GeometryObservation:
    extraction_method: str
    model_family: str | None = None
    layers_examined: tuple[str, ...] = ()
    summary: str = ""
    metrics: tuple[MetricObservation, ...] = ()


@dataclass(frozen=True, slots=True)
class InterventionObservation:
    intervention_method: str
    isolated_measurement_profile: str
    model_mutation_scope: str = "ephemeral_only"
    summary: str = ""
    metrics: tuple[MetricObservation, ...] = ()


@dataclass(frozen=True, slots=True)
class MindOntologyProbeReceipt:
    probe_id: str
    probe_mode: MindOntologyProbeMode
    model_id: str
    provider: str | None = None
    model_revision: str | None = None
    generator_id: str | None = None
    generator_version: str | None = None
    generated_at: str | None = None
    reference_population_ids: tuple[str, ...] = ()
    behavioral_observations: tuple[BehavioralObservation, ...] = ()
    geometry_observations: tuple[GeometryObservation, ...] = ()
    intervention_observations: tuple[InterventionObservation, ...] = ()
    negative_control_results: tuple[str, ...] = ()
    interpretation: MindOntologyInterpretation = MindOntologyInterpretation.INCONCLUSIVE
    causal_support: MindOntologyCausalSupport = MindOntologyCausalSupport.OBSERVATIONAL_ONLY
    limitations: tuple[str, ...] = ()
    provenance: AdapterProvenance = AdapterProvenance.UNAVAILABLE
    source: SourceIdentity | None = None
    receipt: ReceiptRef | None = None
    schema_version: str = field(default="mind-ontology-probe-0.1", init=False)

    def __post_init__(self) -> None:
        if self.probe_mode is MindOntologyProbeMode.BEHAVIORAL_BLACK_BOX:
            if self.geometry_observations or self.intervention_observations:
                raise ValueError(
                    "behavioral_black_box receipts must not carry geometry or intervention observations"
                )
        if self.probe_mode is MindOntologyProbeMode.REPRESENTATIONAL_WHITE_BOX:
            if self.intervention_observations:
                raise ValueError(
                    "representational_white_box receipts must not carry intervention observations"
                )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
