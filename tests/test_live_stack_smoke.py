from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from trusted_runtime.smoke import LiveStackRequirementError, run_live_stack_smoke


def test_live_stack_smoke_writes_machine_readable_artifact(tmp_path: Path):
    case_path = Path(__file__).resolve().parents[1] / "examples" / "ai_agent_shell_access.json"
    artifact = run_live_stack_smoke(case_path, tmp_path)
    assert "smoke_test" in artifact
    assert (tmp_path / "live_stack_smoke.json").exists()
    assert (tmp_path / "smoke_decision_output.json").exists()
    assert (tmp_path / "smoke_decision_report.md").exists()

    payload = json.loads((tmp_path / "live_stack_smoke.json").read_text(encoding="utf-8"))
    assert payload["smoke_test"]["runtime_disposition"] in {"HALT", "CONFIRM_HUMAN", "PROCEED", "SUSPEND"}
    assert "integration_mode" in payload["smoke_test"]
    assert "adapter_provenance" in payload["smoke_test"]


def test_live_stack_smoke_require_all_real_fails_closed_when_not_all_real(tmp_path: Path):
    case_path = Path(__file__).resolve().parents[1] / "examples" / "ai_agent_shell_access.json"
    with patch("trusted_runtime.smoke.adapter_status", return_value={"integration_mode": "partial", "adapters": {}}):
        with pytest.raises(LiveStackRequirementError):
            run_live_stack_smoke(case_path, tmp_path, require_all_real=True)
