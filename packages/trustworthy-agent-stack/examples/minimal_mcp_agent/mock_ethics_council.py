"""Small mock of EthicsCouncil for the minimal end-to-end proof."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Dict, Any


@dataclass(frozen=True)
class HazardMap:
    hazard_map_id: str
    action_description: str
    overall_risk: str
    convergences: List[str]
    fault_lines: List[str]
    suspension_triggers: List[str]
    minority_reports: List[str]
    recommendation: str

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


class MockEthicsCouncil:
    """Deterministic hazard map generator.

    This is intentionally tiny. The important property is that the hazard map
    drives gate behavior rather than merely being printed.
    """

    def evaluate_action(self, action_description: str, risk_level: str = "medium") -> HazardMap:
        if risk_level == "high":
            return HazardMap(
                hazard_map_id="haz_ethics_091",
                action_description=action_description,
                overall_risk="high",
                convergences=["irreversibility", "consent"],
                fault_lines=["authority_vs_utility"],
                suspension_triggers=["file_write", "external_api"],
                minority_reports=["virtue_ethics_concerns_scope_creep"],
                recommendation="require_explicit_confirmation",
            )

        return HazardMap(
            hazard_map_id="haz_ethics_042",
            action_description=action_description,
            overall_risk="medium",
            convergences=["traceability"],
            fault_lines=[],
            suspension_triggers=[],
            minority_reports=[],
            recommendation="proceed_with_logging",
        )


def hazard_to_required_gates(hazard: HazardMap) -> Dict[str, str]:
    """Formal minimal mapping from normative hazard map to operational gates."""
    gates = {
        "manifest_integrity": "pass",
        "least_privilege": "pass",
    }

    if hazard.recommendation == "require_explicit_confirmation" or "consent" in hazard.convergences:
        gates["consent_traceability"] = "escalate"
    else:
        gates["consent_traceability"] = "pass"

    if "irreversibility" in hazard.convergences:
        gates["irreversibility"] = "escalate"

    return gates
