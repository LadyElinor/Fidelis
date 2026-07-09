from __future__ import annotations

from runtime.models import CaseInput, LensResult


def evaluate(case: CaseInput) -> LensResult:
    hazards: list[str] = []
    verdict = "clear"

    if case.context.deployment_pressure in {"medium", "high"}:
        hazards.append("execution_pressure_present")
    if case.context.reversible != "full":
        hazards.append("limited_reversibility")

    if len(hazards) >= 2:
        verdict = "caution"

    return LensResult(
        lens="stoic",
        verdict=verdict,
        hazards=hazards,
        confidence=0.68,
        justification="Flags actions that outrun disciplined control, especially under pressure with limited reversibility.",
        minority_report=False,
    )
