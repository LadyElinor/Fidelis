from __future__ import annotations

from runtime.models import CaseInput, LensResult, MeaningAssayResult


def evaluate(case: CaseInput, lens_results: list[LensResult]) -> MeaningAssayResult:
    significance = 0.1
    warrant = 0.75
    reasoning: list[str] = []

    if case.context.data_contains_personal_information:
        significance += 0.25
        reasoning.append("Action affects personal data.")
    if case.context.reversible != "full":
        significance += 0.25
        reasoning.append("Reversibility is limited.")
    if case.context.deployment_pressure in {"medium", "high"}:
        significance += 0.2
        reasoning.append("Execution pressure increases practical consequence.")
    if case.context.claimed_anonymized and case.context.data_contains_personal_information:
        significance += 0.1
        reasoning.append("Anonymization claims still leave consequential residual risk.")

    if case.authority.authorization_basis == "unclear":
        warrant -= 0.15
        reasoning.append("Authority basis is unclear.")
    if not case.context.retention_policy_clear:
        warrant -= 0.15
        reasoning.append("Retention basis is unclear.")
    if not case.context.human_approval_present and significance >= 0.4:
        warrant -= 0.1
        reasoning.append("No human approval is present for a consequential case.")
    if any(l.verdict == "object" for l in lens_results):
        warrant -= 0.15
        reasoning.append("At least one ethical lens raised a hard objection.")
    if case.authority.authorization_basis != "unclear" and case.context.human_approval_present:
        warrant += 0.1
        reasoning.append("Clear authority and human approval strengthen warrant.")

    significance = max(0.0, min(1.0, significance))
    warrant = max(0.0, min(1.0, warrant))

    return MeaningAssayResult(significance=significance, warrant=warrant, reasoning=reasoning)
