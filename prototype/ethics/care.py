from __future__ import annotations

from runtime.models import CaseInput, LensResult


def evaluate(case: CaseInput) -> LensResult:
    hazards: list[str] = []
    verdict = "clear"

    has_affected_party_burden = False
    if case.context.data_contains_personal_information:
        hazards.append("dependent_or_unrepresented_parties_affected")
        has_affected_party_burden = True
    if not case.context.retention_policy_clear:
        hazards.append("relationship_burden_without_clear_retention_boundary")
        has_affected_party_burden = True
    if case.authority.authorization_basis == "unclear":
        hazards.append("insufficient_relational_accountability")

    if has_affected_party_burden:
        verdict = "object"
    elif hazards:
        verdict = "caution"

    return LensResult(
        lens="care",
        verdict=verdict,
        hazards=hazards,
        confidence=0.77,
        justification="Flags burdens placed on affected parties who cannot easily inspect, contest, or reverse the action.",
        minority_report=False,
    )
