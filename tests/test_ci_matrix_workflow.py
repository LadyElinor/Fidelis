from __future__ import annotations

from pathlib import Path


def test_ci_matrix_all_real_job_uses_truthfulness_gated_smoke():
    workflow_path = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci-matrix.yml"
    text = workflow_path.read_text(encoding="utf-8")

    assert "all-real-smoke:" in text
    assert "Live stack smoke truthfulness gate" in text
    assert "trusted-runtime live-stack-smoke --input examples/ai_agent_shell_access.json --output .ci-artifacts --require-all-real" in text
    assert "live_stack_smoke.json" in text
