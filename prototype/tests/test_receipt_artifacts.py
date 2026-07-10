import json
from pathlib import Path

from runtime.orchestrator import run_case

EXAMPLE_CASE = Path(__file__).resolve().parents[1] / "examples" / "customer_log_processing.json"


def test_receipts_include_provenance_and_runtime_decision_details() -> None:
    summary = run_case(str(EXAMPLE_CASE))
    artifacts_dir = Path(summary["artifacts_dir"])

    provenance = json.loads((artifacts_dir / "provenance.json").read_text(encoding="utf-8"))
    decision = json.loads((artifacts_dir / "runtime_decision.json").read_text(encoding="utf-8"))

    assert provenance["provenance_status"] == "partial"
    assert provenance["hash"].startswith("sha256:")
    assert decision["degradation_policy_row"] == "unresolved_hard_objection"
    assert decision["route_quality"]["authority_or_provenance"] == "degraded"
    assert decision["coverage_records"]
    assert decision["evidence_records"]


def test_override_receipt_marks_overridden_dissent() -> None:
    summary = run_case(
        str(EXAMPLE_CASE),
        override_requested=True,
        override_source="human_reviewer",
        override_rationale="Operational urgency accepted with explicit documented override.",
    )
    decision = json.loads((Path(summary["artifacts_dir"]) / "runtime_decision.json").read_text(encoding="utf-8"))
    assert decision["override_record"]["approved"] is True
    assert any(record["resolution_status"] == "overridden" for record in decision["dissent_records"])
