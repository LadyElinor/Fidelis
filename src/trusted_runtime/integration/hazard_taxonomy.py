"""Phase 2: hazard taxonomy with initial/residual risk levels.

Structural model adapted from the Riskman ontology (Gorczyca, Arndt, Diller,
Hampe, Heidenreich, Kettmann, Kroetzsch, Mennicke, Rudolph, Strass,
"Supporting Risk Management for Medical Devices via the Riskman Ontology and
Shapes", SEMANTiCS 2025; https://w3id.org/riskman), itself built on ISO 14971.

The OWL/SHACL machinery is deliberately not adopted. This runtime is a
closed-world Python decision engine, so the model is ported without importing
Riskman's certification substrate.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class HazardFamily(str, Enum):
    SAFETY_INVARIANT = "safety_invariant"
    IRREVERSIBILITY = "irreversibility"
    FORMATION = "formation"
    SECURITY = "security"
    AUTONOMY = "autonomy"
    PROVENANCE = "provenance"
    CONTESTED_VALUE = "contested_value"
    UNCLASSIFIED = "unclassified"


class RiskLevel(int, Enum):
    NEGLIGIBLE = 0
    LOW = 1
    MODERATE = 2
    SERIOUS = 3
    SEVERE = 4


_FAMILY_INITIAL_FLOOR: dict[HazardFamily, RiskLevel] = {
    HazardFamily.SAFETY_INVARIANT: RiskLevel.SEVERE,
    HazardFamily.IRREVERSIBILITY: RiskLevel.SERIOUS,
    HazardFamily.SECURITY: RiskLevel.SERIOUS,
    HazardFamily.FORMATION: RiskLevel.MODERATE,
    HazardFamily.AUTONOMY: RiskLevel.MODERATE,
    HazardFamily.PROVENANCE: RiskLevel.MODERATE,
    HazardFamily.CONTESTED_VALUE: RiskLevel.LOW,
    HazardFamily.UNCLASSIFIED: RiskLevel.MODERATE,
}


class MitigationIncreasesRiskError(ValueError):
    """Raised when a mitigation would raise residual risk above initial risk."""


@dataclass(frozen=True)
class LeveledHazard:
    family: HazardFamily
    raw_label: str
    initial_level: RiskLevel
    residual_level: RiskLevel
    mitigations: tuple[str, ...] = ()
    rationale: str = ""

    @property
    def mitigation_delta(self) -> int:
        return self.initial_level.value - self.residual_level.value

    @property
    def is_mitigated(self) -> bool:
        return self.residual_level.value < self.initial_level.value


_FAMILY_SIGNALS: tuple[tuple[HazardFamily, tuple[str, ...]], ...] = (
    (HazardFamily.FORMATION, ("formation::", "canonization", "scale_without_consent")),
    (HazardFamily.SAFETY_INVARIANT, ("invariant", "safety-critical", "safety_invariant")),
    (HazardFamily.SECURITY, ("security", "confidential", "integrity", "availability")),
    (HazardFamily.IRREVERSIBILITY, ("irreversib", "cannot be undone", "permanent")),
    (HazardFamily.AUTONOMY, ("autonom", "unsupervised", "self-modif", "expand scope")),
    (HazardFamily.PROVENANCE, ("provenance", "unverified claim", "claimed real")),
    (HazardFamily.CONTESTED_VALUE, ("contested", "disagree", "minority")),
)


def classify_hazard(raw_label: str) -> HazardFamily:
    text = (raw_label or "").lower()
    for family, signals in _FAMILY_SIGNALS:
        if any(signal in text for signal in signals):
            return family
    return HazardFamily.UNCLASSIFIED


def level_hazard(raw_label: str, *, initial_override: RiskLevel | None = None) -> LeveledHazard:
    family = classify_hazard(raw_label)
    initial = initial_override or _FAMILY_INITIAL_FLOOR[family]
    return LeveledHazard(
        family=family,
        raw_label=raw_label,
        initial_level=initial,
        residual_level=initial,
        rationale=(
            f"classified as {family.value}; initial level {initial.name} "
            f"({'override' if initial_override else 'family floor'})"
        ),
    )


def apply_mitigations(
    hazard: LeveledHazard,
    residual_level: RiskLevel,
    mitigations: tuple[str, ...],
) -> LeveledHazard:
    if residual_level.value > hazard.initial_level.value:
        raise MitigationIncreasesRiskError(
            f"mitigation of '{hazard.raw_label}' would raise residual risk from "
            f"{hazard.initial_level.name} to {residual_level.name}; a mitigation must never increase risk"
        )
    return LeveledHazard(
        family=hazard.family,
        raw_label=hazard.raw_label,
        initial_level=hazard.initial_level,
        residual_level=residual_level,
        mitigations=mitigations,
        rationale=hazard.rationale + f"; mitigated to {residual_level.name} by {len(mitigations)} SDA(s)",
    )


def assert_mitigation_does_not_increase_risk(initial_level: RiskLevel, residual_level: RiskLevel) -> None:
    if residual_level.value > initial_level.value:
        raise MitigationIncreasesRiskError(
            f"residual {residual_level.name} exceeds initial {initial_level.name}: a mitigation must never increase risk"
        )


@dataclass(frozen=True)
class HazardProfile:
    hazards: tuple[LeveledHazard, ...]

    @property
    def families_present(self) -> tuple[str, ...]:
        return tuple(sorted({h.family.value for h in self.hazards}))

    @property
    def max_initial_level(self) -> RiskLevel:
        return max((h.initial_level for h in self.hazards), default=RiskLevel.NEGLIGIBLE)

    @property
    def max_residual_level(self) -> RiskLevel:
        return max((h.residual_level for h in self.hazards), default=RiskLevel.NEGLIGIBLE)

    @property
    def unclassified_count(self) -> int:
        return sum(1 for h in self.hazards if h.family is HazardFamily.UNCLASSIFIED)


def build_hazard_profile(raw_labels: tuple[str, ...]) -> HazardProfile:
    return HazardProfile(tuple(level_hazard(label) for label in raw_labels))
