from pathlib import Path

from runtime.gating import DEGRADATION_POLICY
from runtime.orchestrator import run_case

EXAMPLE_CASE = Path(__file__).resolve().parents[1] / "examples" / "customer_log_processing.json"


def test_demo_case_reports_policy_and_dissent() -> None:
    summary = run_case(str(EXAMPLE_CASE))
    assert summary["degradation_policy_row"] == "unresolved_hard_objection"
    assert summary["human_escalation_required"] is True
    assert len(summary["dissent_records"]) >= 2
    assert "degraded_authority_or_provenance_route" in summary["co_dependency_flags"]
    assert summary["route_quality"]["telemetry"] == "strong"


def test_degradation_policy_contains_core_rows() -> None:
    assert "unresolved_hard_objection" in DEGRADATION_POLICY
    assert "co_dependent_evidence_routes" in DEGRADATION_POLICY
    assert "all_required_checks_passed" in DEGRADATION_POLICY
