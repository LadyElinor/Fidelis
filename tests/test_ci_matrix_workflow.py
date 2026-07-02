from __future__ import annotations

from pathlib import Path


def test_ci_matrix_all_real_job_asserts_fail_closed_on_generic_runners():
    workflow_path = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci-matrix.yml"
    text = workflow_path.read_text(encoding="utf-8")

    # Generic runners cannot be all-real, so the job must test the gate
    # itself: --require-all-real must fail closed with the named reason.
    assert "all-real-gate-fails-closed:" in text
    assert "trusted-runtime live-stack-smoke --input examples/ai_agent_shell_access.json --output .ci-artifacts --require-all-real" in text
    assert "TRUTHFULNESS GATE FAILED OPEN" in text
    assert 'grep -q "requires all-real integration mode"' in text
    assert "live_stack_smoke.json" in text
    # A permanently-red scheduled job is a standing false alarm; the always-
    # failing form of this job must not come back.
    assert "all-real-smoke:" not in text


def test_ci_matrix_stub_job_installs_test_dependencies():
    workflow_path = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci-matrix.yml"
    text = workflow_path.read_text(encoding="utf-8")

    assert 'pip install -e ".[test]"' in text
    assert "python -m pytest -q" in text
