from __future__ import annotations

from pathlib import Path

from ethics import care, kantian, stoic
from meaning import assay
from telemetry import checks, vector
from runtime.dependency_graph import analyze_evidence_routes, build_dependency_graph
from runtime.loader import InputValidationRuntimeError, load_and_validate
from runtime.models import RuntimeDecisionResult
from runtime.provenance import evaluate_authority_provenance
from runtime.receipts import write_all_receipts


def run_case(
    path: str,
    *,
    force_missing_meaning: bool = False,
    force_missing_telemetry: bool = False,
    force_malformed_meaning: bool = False,
    force_malformed_telemetry: bool = False,
    force_malformed_provenance: bool = False,
    override_requested: bool = False,
    override_source: str | None = None,
    override_rationale: str | None = None,
) -> dict:
    input_path = Path(path)

    try:
        case = load_and_validate(input_path)
    except InputValidationRuntimeError:
        raise

    lens_results = [
        kantian.evaluate(case),
        stoic.evaluate(case),
        care.evaluate(case),
    ]
    meaning_result = assay.evaluate(case, lens_results)
    telemetry_vector = vector.compute(case, lens_results, meaning_result)

    if force_missing_meaning:
        meaning_result.available = False
        meaning_result.reasoning.append("Meaning-assay output intentionally suppressed for degradation test.")
    if force_malformed_meaning:
        meaning_result.malformed = True
        meaning_result.reasoning.append("Meaning-assay output intentionally malformed for degradation test.")
    if force_missing_telemetry:
        telemetry_vector.available = False
    if force_malformed_telemetry:
        telemetry_vector.malformed = True
    telemetry_flags = checks.evaluate(telemetry_vector)
    provenance_assessment = evaluate_authority_provenance(case)
    if force_malformed_provenance:
        provenance_assessment["malformed"] = True
        provenance_assessment.setdefault("notes", []).append("Provenance output intentionally malformed for degradation test.")
    dependency_graph = build_dependency_graph(case, lens_results, meaning_result, telemetry_vector, provenance_assessment)
    independent_evidence_routes, co_dependency_flags, integrity_rationale, route_quality = analyze_evidence_routes(dependency_graph)
    integrity_rationale.extend(provenance_assessment.get("notes", []))

    from runtime.gating import decide

    decision: RuntimeDecisionResult = decide(
        case=case,
        lens_results=lens_results,
        meaning=meaning_result,
        telemetry_vector=telemetry_vector,
        telemetry_flags=telemetry_flags,
        provenance_assessment=provenance_assessment,
        independent_evidence_routes=independent_evidence_routes,
        co_dependency_flags=co_dependency_flags,
        integrity_rationale=integrity_rationale,
        route_quality=route_quality,
        override_requested=override_requested,
        override_source=override_source,
        override_rationale=override_rationale,
    )

    receipts_info = write_all_receipts(
        base_dir=input_path.parent.parent / "receipts",
        case_payload=case.model_dump(),
        lens_results=[item.model_dump() for item in lens_results],
        meaning_payload=meaning_result.model_dump(),
        telemetry_payload={
            "vector": telemetry_vector.model_dump(),
            "flags": telemetry_flags,
        },
        provenance_payload=provenance_assessment,
        dependency_graph=dependency_graph,
        decision=decision,
    )

    decision.receipt_hash = receipts_info["decision_hash"]

    return {
        **decision.model_dump(),
        "artifacts_dir": receipts_info["artifacts_dir"],
        "final_chain_hash": receipts_info["final_chain_hash"],
    }
