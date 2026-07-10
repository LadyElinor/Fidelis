from pathlib import Path

from runtime.orchestrator import run_case

EXAMPLE_CASE = Path(__file__).resolve().parents[1] / "examples" / "customer_log_processing.json"


def test_malformed_meaning_assay_degrades_to_failed_review() -> None:
    summary = run_case(str(EXAMPLE_CASE), force_malformed_meaning=True)
    assert summary["runtime_decision"] == "REVIEW"
    assert summary["runtime_disposition"] == "SUSPEND"
    assert summary["decision_integrity"] == "FAILED"
    assert summary["degradation_policy_row"] == "malformed_meaning_assay"


def test_malformed_telemetry_degrades_to_failed_review() -> None:
    summary = run_case(str(EXAMPLE_CASE), force_malformed_telemetry=True)
    assert summary["runtime_decision"] == "REVIEW"
    assert summary["runtime_disposition"] == "SUSPEND"
    assert summary["decision_integrity"] == "FAILED"
    assert summary["degradation_policy_row"] == "malformed_telemetry"


def test_malformed_provenance_degrades_to_failed_review() -> None:
    summary = run_case(str(EXAMPLE_CASE), force_malformed_provenance=True)
    assert summary["runtime_decision"] == "REVIEW"
    assert summary["runtime_disposition"] == "SUSPEND"
    assert summary["decision_integrity"] == "FAILED"
    assert summary["degradation_policy_row"] == "malformed_provenance"
