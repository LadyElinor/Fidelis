import json
from pathlib import Path

from runtime.orchestrator import run_case

EXAMPLE_DIR = Path(__file__).resolve().parents[1] / "examples"
EXAMPLE_CASE = EXAMPLE_DIR / "customer_log_processing.json"


def test_dependency_graph_emits_authority_route() -> None:
    summary = run_case(str(EXAMPLE_CASE))
    graph_path = Path(summary["artifacts_dir"]) / "dependency_graph.json"
    assert graph_path.exists()
    payload = json.loads(graph_path.read_text(encoding="utf-8"))
    assert any(node["kind"] == "authority_or_provenance" for node in payload["nodes"])
    assert "authority_or_provenance" not in summary["independent_evidence_routes"]
    assert "degraded_authority_or_provenance_route" in summary["co_dependency_flags"]


def test_low_risk_case_can_proceed_when_routes_are_independent() -> None:
    mutated = json.loads(EXAMPLE_CASE.read_text(encoding="utf-8"))
    mutated["case_id"] = "case-customer-log-processing-low-risk"
    mutated["action"]["name"] = "update_internal_routing_metadata"
    mutated["action"]["description"] = "Update internal routing metadata for support workflow tuning."
    mutated["context"]["data_contains_personal_information"] = False
    mutated["context"]["claimed_anonymized"] = False
    mutated["context"]["retention_policy_clear"] = True
    mutated["context"]["reversible"] = "full"
    mutated["context"]["human_approval_present"] = True
    mutated["context"]["deployment_pressure"] = "low"
    mutated["authority"]["authorization_basis"] = "clear"

    out_path = EXAMPLE_DIR / "customer_log_processing_low_risk.json"
    out_path.write_text(json.dumps(mutated, indent=2) + "\n", encoding="utf-8")
    try:
        summary = run_case(str(out_path))
    finally:
        out_path.unlink(missing_ok=True)

    assert summary["runtime_decision"] == "PROCEED"
    assert summary["decision_integrity"] == "FULL"
    assert summary["degradation_policy_row"] == "all_required_checks_passed"
    assert not summary["co_dependency_flags"]
    assert summary["route_quality"]["authority_or_provenance"] == "strong"


def test_degraded_authority_route_triggers_review_without_other_failures() -> None:
    mutated = json.loads(EXAMPLE_CASE.read_text(encoding="utf-8"))
    mutated["case_id"] = "case-customer-log-processing-degraded-authority"
    mutated["action"]["name"] = "update_internal_routing_metadata"
    mutated["action"]["description"] = "Update internal routing metadata for support workflow tuning."
    mutated["context"]["data_contains_personal_information"] = False
    mutated["context"]["claimed_anonymized"] = False
    mutated["context"]["retention_policy_clear"] = True
    mutated["context"]["reversible"] = "full"
    mutated["context"]["human_approval_present"] = True
    mutated["context"]["deployment_pressure"] = "low"
    mutated["claims"]["operator_justification"] = "Low-risk internal routing metadata update with documented operational purpose."
    mutated["authority"]["authorization_basis"] = "unclear"
    mutated["authority"]["requester_role"] = "internal_agent"

    out_path = EXAMPLE_DIR / "customer_log_processing_degraded_authority.json"
    out_path.write_text(json.dumps(mutated, indent=2) + "\n", encoding="utf-8")
    try:
        summary = run_case(str(out_path))
    finally:
        out_path.unlink(missing_ok=True)

    assert summary["runtime_decision"] == "REVIEW"
    assert summary["decision_integrity"] == "PARTIAL"
    assert "degraded_authority_or_provenance_route" in summary["co_dependency_flags"]
    assert summary["route_quality"]["authority_or_provenance"] == "degraded"
    assert summary["degradation_policy_row"] == "co_dependent_evidence_routes"
