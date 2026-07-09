from __future__ import annotations

from runtime.models import CaseInput, LensResult, MeaningAssayResult, RuntimeDecisionResult, TelemetryVector


def decide(
    case: CaseInput,
    lens_results: list[LensResult],
    meaning: MeaningAssayResult,
    telemetry_vector: TelemetryVector,
    telemetry_flags: list[str],
) -> RuntimeDecisionResult:
    unresolved_dissent = [item.lens for item in lens_results if item.verdict == "object"]

    if any(flag == "irreversible_high_agency_action" for flag in telemetry_flags):
        return RuntimeDecisionResult(
            case_id=case.case_id,
            runtime_decision="HALT",
            risk_state="RED",
            decision_integrity="FULL",
            reason="irreversible_high_agency_action",
            unresolved_dissent=unresolved_dissent,
        )

    if unresolved_dissent:
        return RuntimeDecisionResult(
            case_id=case.case_id,
            runtime_decision="HALT",
            risk_state="RED",
            decision_integrity="FULL",
            reason="unresolved_hard_objection",
            unresolved_dissent=unresolved_dissent,
        )

    if meaning.significance >= 0.75 and meaning.warrant < 0.60:
        return RuntimeDecisionResult(
            case_id=case.case_id,
            runtime_decision="HALT",
            risk_state="RED",
            decision_integrity="FULL",
            reason="high_agency_without_sufficient_warrant",
            unresolved_dissent=unresolved_dissent,
        )

    if any(flag == "weak_independence" for flag in telemetry_flags):
        return RuntimeDecisionResult(
            case_id=case.case_id,
            runtime_decision="REVIEW",
            risk_state="AMBER",
            decision_integrity="PARTIAL",
            reason="weak_independence",
            unresolved_dissent=unresolved_dissent,
        )

    return RuntimeDecisionResult(
        case_id=case.case_id,
        runtime_decision="PROCEED",
        risk_state="GREEN",
        decision_integrity="FULL",
        reason="all_required_checks_passed",
        unresolved_dissent=unresolved_dissent,
    )
