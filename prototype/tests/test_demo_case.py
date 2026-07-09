from pathlib import Path

from runtime.orchestrator import run_case


def test_demo_case_halts_and_writes_receipts() -> None:
    summary = run_case("examples/customer_log_processing.json")
    assert summary["runtime_decision"] == "HALT"
    artifacts_dir = Path(summary["artifacts_dir"])
    assert artifacts_dir.exists()
    assert (artifacts_dir / "receipt_chain.json").exists()
