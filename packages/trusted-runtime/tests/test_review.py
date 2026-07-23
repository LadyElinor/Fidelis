from __future__ import annotations

import json
from pathlib import Path

from trusted_runtime.review import run_review_input


ALLOWED_L4_STATUSES = {"VALIDATED", "CALIBRATING", "FAILED", "UNAVAILABLE"}


def test_run_review_input_writes_curated_export_payload(tmp_path: Path):
    case_path = Path(__file__).resolve().parents[1] / "examples" / "ai_agent_shell_access.json"

    run_review_input(case_path, tmp_path)

    payload = json.loads((tmp_path / "decision_output.json").read_text(encoding="utf-8"))
    assert "l4_interpretation" in payload
    assert payload["cer_bundle"]["sophron_validation"]["validation_status"] in ALLOWED_L4_STATUSES
    assert payload["cer_bundle"]["sophron_validation"]["interpretation"] == payload["l4_interpretation"]
    assert (tmp_path / "decision_report.md").exists()
