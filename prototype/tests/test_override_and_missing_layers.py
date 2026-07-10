from pathlib import Path

from runtime.orchestrator import run_case

EXAMPLE_CASE = Path(__file__).resolve().parents[1] / "examples" / "customer_log_processing.json"


def test_override_can_force_proceed_with_dissent_and_rationale() -> None:
    summary = run_case(
        str(EXAMPLE_CASE),
        override_requested=True,
        override_source="human_reviewer",
        override_rationale="Operational urgency accepted with explicit documented override.",
    )
    assert summary["runtime_decision"] == "PROCEED"
    assert summary["decision_integrity"] == "PARTIAL"
    assert summary["degradation_policy_row"] == "override_with_dissent"
    assert summary["override_record"]["approved"] is True
    assert all(record["resolution_status"] == "overridden" for record in summary["dissent_records"] if record["source"] in {"kantian", "care"})


def test_missing_meaning_assay_degrades_to_failed_review() -> None:
    summary = run_case(str(EXAMPLE_CASE), force_missing_meaning=True)
    assert summary["runtime_decision"] == "REVIEW"
    assert summary["decision_integrity"] == "FAILED"
    assert summary["degradation_policy_row"] == "missing_meaning_assay"


def test_missing_telemetry_degrades_to_failed_review() -> None:
    summary = run_case(str(EXAMPLE_CASE), force_missing_telemetry=True)
    assert summary["runtime_decision"] == "REVIEW"
    assert summary["decision_integrity"] == "FAILED"
    assert summary["degradation_policy_row"] == "missing_telemetry"


def test_missing_provenance_degrades_to_failed_review() -> None:
    summary = run_case(str(EXAMPLE_CASE).replace("customer_log_processing.json", "customer_log_processing_missing_provenance.json"))
    assert summary["runtime_decision"] == "REVIEW"
    assert summary["decision_integrity"] == "FAILED"
    assert summary["degradation_policy_row"] == "missing_provenance"
