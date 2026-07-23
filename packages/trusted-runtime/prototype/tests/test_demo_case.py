from pathlib import Path

from runtime.orchestrator import run_case

EXAMPLE_CASE = Path(__file__).resolve().parents[1] / "examples" / "customer_log_processing.json"


def test_demo_case_halts_and_writes_receipts() -> None:
    summary = run_case(str(EXAMPLE_CASE))
    assert summary["runtime_decision"] == "HALT"
    artifacts_dir = Path(summary["artifacts_dir"])
    assert artifacts_dir.exists()
    assert (artifacts_dir / "receipt_chain.json").exists()
    assert (artifacts_dir / "dependency_graph.json").exists()
    assert (artifacts_dir / "provenance.json").exists()
    assert summary["unresolved_dissent"] == ["kantian", "care"]
    assert summary["dissent_records"]
    assert "authority_or_provenance" not in summary["independent_evidence_routes"]
