from __future__ import annotations

from runtime.models import CaseInput, LensResult


def evaluate(case: CaseInput) -> LensResult:
    hazards: list[str] = []
    verdict = "clear"

    if case.context.data_contains_personal_information and case.authority.authorization_basis == "unclear":
        hazards.append("consent_or_authority_unclear")
    if case.context.data_contains_personal_information and not case.context.retention_policy_clear:
        hazards.append("persons_used_without_clear_retention_basis")

    if hazards:
        verdict = "object"

    return LensResult(
        lens="kantian",
        verdict=verdict,
        hazards=hazards,
        confidence=0.74,
        justification="Flags rights/authority concerns when personal data use proceeds without clear consent, authority, or retention basis.",
        minority_report=False,
    )
