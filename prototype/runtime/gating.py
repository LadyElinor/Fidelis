from __future__ import annotations

from runtime.models import (
    CaseInput,
    CoverageRecord,
    DissentRecord,
    EvidenceRecord,
    LensResult,
    MeaningAssayResult,
    OverrideRecord,
    RuntimeDecisionResult,
    TelemetryVector,
)


DEGRADATION_POLICY = {
    "missing_provenance": {
        "runtime_decision": "REVIEW",
        "runtime_disposition": "SUSPEND",
        "risk_state": "AMBER",
        "decision_integrity": "FAILED",
        "human_escalation_required": True,
    },
    "malformed_lens_output": {
        "runtime_decision": "REVIEW",
        "runtime_disposition": "SUSPEND",
        "risk_state": "AMBER",
        "decision_integrity": "FAILED",
        "human_escalation_required": True,
    },
    "malformed_provenance": {
        "runtime_decision": "REVIEW",
        "runtime_disposition": "SUSPEND",
        "risk_state": "AMBER",
        "decision_integrity": "FAILED",
        "human_escalation_required": True,
    },
    "missing_meaning_assay": {
        "runtime_decision": "REVIEW",
        "runtime_disposition": "SUSPEND",
        "risk_state": "AMBER",
        "decision_integrity": "FAILED",
        "human_escalation_required": True,
    },
    "malformed_meaning_assay": {
        "runtime_decision": "REVIEW",
        "runtime_disposition": "SUSPEND",
        "risk_state": "AMBER",
        "decision_integrity": "FAILED",
        "human_escalation_required": True,
    },
    "missing_telemetry": {
        "runtime_decision": "REVIEW",
        "runtime_disposition": "SUSPEND",
        "risk_state": "AMBER",
        "decision_integrity": "FAILED",
        "human_escalation_required": True,
    },
    "malformed_telemetry": {
        "runtime_decision": "REVIEW",
        "runtime_disposition": "SUSPEND",
        "risk_state": "AMBER",
        "decision_integrity": "FAILED",
        "human_escalation_required": True,
    },
    "override_with_dissent": {
        "runtime_decision": "PROCEED",
        "runtime_disposition": "CONFIRM_HUMAN",
        "risk_state": "AMBER",
        "decision_integrity": "PARTIAL",
        "human_escalation_required": True,
    },
    "irreversible_high_agency_action": {
        "runtime_decision": "HALT",
        "runtime_disposition": "SUSPEND",
        "risk_state": "RED",
        "decision_integrity": "FULL",
        "human_escalation_required": True,
    },
    "unresolved_hard_objection": {
        "runtime_decision": "HALT",
        "runtime_disposition": "SUSPEND",
        "risk_state": "RED",
        "decision_integrity": "FULL",
        "human_escalation_required": True,
    },
    "high_agency_without_sufficient_warrant": {
        "runtime_decision": "HALT",
        "runtime_disposition": "SUSPEND",
        "risk_state": "RED",
        "decision_integrity": "PARTIAL",
        "human_escalation_required": True,
    },
    "weak_independence": {
        "runtime_decision": "REVIEW",
        "runtime_disposition": "CONFIRM_HUMAN",
        "risk_state": "AMBER",
        "decision_integrity": "PARTIAL",
        "human_escalation_required": True,
    },
    "co_dependent_evidence_routes": {
        "runtime_decision": "REVIEW",
        "runtime_disposition": "CONFIRM_HUMAN",
        "risk_state": "AMBER",
        "decision_integrity": "PARTIAL",
        "human_escalation_required": True,
    },
    "all_required_checks_passed": {
        "runtime_decision": "PROCEED",
        "runtime_disposition": "PROCEED",
        "risk_state": "GREEN",
        "decision_integrity": "FULL",
        "human_escalation_required": False,
    },
}


def _dissent_records(lens_results: list[LensResult]) -> list[DissentRecord]:
    records: list[DissentRecord] = []
    for item in lens_results:
        if item.verdict in {"object", "caution"}:
            records.append(
                DissentRecord(
                    source=item.lens,
                    severity=item.verdict,
                    hazards=item.hazards,
                    justification=item.justification,
                    resolution_status="unresolved",
                )
            )
    return records


def _coverage_mode_for_quality(quality: str) -> str:
    if quality == "missing":
        return "missing"
    if quality in {"moderate", "degraded"}:
        return "derived-advisory"
    return "direct-real"


def _evidence_class_for_quality(quality: str) -> str:
    if quality == "degraded":
        return "degraded"
    if quality == "moderate":
        return "derived"
    if quality == "missing":
        return "unknown"
    return "independent"


def _build_result(
    case: CaseInput,
    reason: str,
    unresolved_dissent: list[str],
    dissent_records: list[DissentRecord],
    independent_evidence_routes: list[str],
    co_dependency_flags: list[str],
    integrity_rationale: list[str],
    route_quality: dict[str, str],
) -> RuntimeDecisionResult:
    policy = DEGRADATION_POLICY[reason]
    coverage_records = [
        CoverageRecord(layer=route, mode=_coverage_mode_for_quality(quality), notes=[])
        for route, quality in route_quality.items()
    ]
    evidence_records = [
        EvidenceRecord(kind="route", source=route, independence_class=_evidence_class_for_quality(quality), notes=[])
        for route, quality in route_quality.items()
    ]
    return RuntimeDecisionResult(
        case_id=case.case_id,
        runtime_decision=policy["runtime_decision"],
        runtime_disposition=policy["runtime_disposition"],
        risk_state=policy["risk_state"],
        decision_integrity=policy["decision_integrity"],
        reason=reason,
        unresolved_dissent=unresolved_dissent,
        dissent_records=dissent_records,
        independent_evidence_routes=independent_evidence_routes,
        co_dependency_flags=co_dependency_flags,
        integrity_rationale=integrity_rationale,
        route_quality=route_quality,
        coverage_records=coverage_records,
        evidence_records=evidence_records,
        degradation_policy_row=reason,
        human_escalation_required=policy["human_escalation_required"],
        override_record=OverrideRecord(),
        receipt_hash="",
        parent_receipts=[],
    )


def decide(
    case: CaseInput,
    lens_results: list[LensResult],
    meaning: MeaningAssayResult,
    telemetry_vector: TelemetryVector,
    telemetry_flags: list[str],
    provenance_assessment: dict[str, object],
    independent_evidence_routes: list[str],
    co_dependency_flags: list[str],
    integrity_rationale: list[str],
    route_quality: dict[str, str],
    override_requested: bool = False,
    override_source: str | None = None,
    override_rationale: str | None = None,
) -> RuntimeDecisionResult:
    unresolved_dissent = [item.lens for item in lens_results if item.verdict == "object"]
    dissent_records = _dissent_records(lens_results)

    if any(item.malformed for item in lens_results):
        result = _build_result(
            case,
            "malformed_lens_output",
            unresolved_dissent,
            dissent_records,
            independent_evidence_routes,
            co_dependency_flags,
            integrity_rationale,
            route_quality,
        )
        result.override_record.override_requested = override_requested
        result.override_record.override_source = override_source
        result.override_record.rationale = override_rationale
        return result

    if provenance_assessment.get("malformed"):
        result = _build_result(
            case,
            "malformed_provenance",
            unresolved_dissent,
            dissent_records,
            independent_evidence_routes,
            co_dependency_flags,
            integrity_rationale,
            route_quality,
        )
        result.override_record.override_requested = override_requested
        result.override_record.override_source = override_source
        result.override_record.rationale = override_rationale
        return result

    if route_quality.get("authority_or_provenance") == "missing":
        result = _build_result(
            case,
            "missing_provenance",
            unresolved_dissent,
            dissent_records,
            independent_evidence_routes,
            co_dependency_flags,
            integrity_rationale,
            route_quality,
        )
        result.override_record.override_requested = override_requested
        result.override_record.override_source = override_source
        result.override_record.rationale = override_rationale
        return result

    if meaning.malformed:
        result = _build_result(
            case,
            "malformed_meaning_assay",
            unresolved_dissent,
            dissent_records,
            independent_evidence_routes,
            co_dependency_flags,
            integrity_rationale,
            route_quality,
        )
        result.override_record.override_requested = override_requested
        result.override_record.override_source = override_source
        result.override_record.rationale = override_rationale
        return result

    if not meaning.available:
        result = _build_result(
            case,
            "missing_meaning_assay",
            unresolved_dissent,
            dissent_records,
            independent_evidence_routes,
            co_dependency_flags,
            integrity_rationale,
            route_quality,
        )
        result.override_record.override_requested = override_requested
        result.override_record.override_source = override_source
        result.override_record.rationale = override_rationale
        return result

    if telemetry_vector.malformed:
        result = _build_result(
            case,
            "malformed_telemetry",
            unresolved_dissent,
            dissent_records,
            independent_evidence_routes,
            co_dependency_flags,
            integrity_rationale,
            route_quality,
        )
        result.override_record.override_requested = override_requested
        result.override_record.override_source = override_source
        result.override_record.rationale = override_rationale
        return result

    if not telemetry_vector.available:
        result = _build_result(
            case,
            "missing_telemetry",
            unresolved_dissent,
            dissent_records,
            independent_evidence_routes,
            co_dependency_flags,
            integrity_rationale,
            route_quality,
        )
        result.override_record.override_requested = override_requested
        result.override_record.override_source = override_source
        result.override_record.rationale = override_rationale
        return result

    if override_requested and unresolved_dissent and override_source and override_rationale:
        result = _build_result(
            case,
            "override_with_dissent",
            unresolved_dissent,
            dissent_records,
            independent_evidence_routes,
            co_dependency_flags,
            integrity_rationale + ["Proceed path invoked only through explicit override with rationale."],
            route_quality,
        )
        result.override_record.override_requested = True
        result.override_record.override_source = override_source
        result.override_record.rationale = override_rationale
        result.override_record.approved = True
        for record in result.dissent_records:
            if record.source in unresolved_dissent:
                record.resolution_status = "overridden"
                record.override_rationale = override_rationale
        return result

    if any(flag == "irreversible_high_agency_action" for flag in telemetry_flags):
        return _build_result(
            case,
            "irreversible_high_agency_action",
            unresolved_dissent,
            dissent_records,
            independent_evidence_routes,
            co_dependency_flags,
            integrity_rationale,
            route_quality,
        )

    if unresolved_dissent:
        return _build_result(
            case,
            "unresolved_hard_objection",
            unresolved_dissent,
            dissent_records,
            independent_evidence_routes,
            co_dependency_flags,
            integrity_rationale,
            route_quality,
        )

    if meaning.significance >= 0.75 and meaning.warrant < 0.60:
        return _build_result(
            case,
            "high_agency_without_sufficient_warrant",
            unresolved_dissent,
            dissent_records,
            independent_evidence_routes,
            co_dependency_flags,
            integrity_rationale,
            route_quality,
        )

    if any(flag == "weak_independence" for flag in telemetry_flags) or co_dependency_flags:
        return _build_result(
            case,
            "co_dependent_evidence_routes" if co_dependency_flags else "weak_independence",
            unresolved_dissent,
            dissent_records,
            independent_evidence_routes,
            co_dependency_flags,
            integrity_rationale,
            route_quality,
        )

    return _build_result(
        case,
        "all_required_checks_passed",
        unresolved_dissent,
        dissent_records,
        independent_evidence_routes,
        co_dependency_flags,
        integrity_rationale,
        route_quality,
    )
