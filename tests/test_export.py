from __future__ import annotations

import json
from pathlib import Path

from trusted_runtime.export import export_decision_payload, to_json_safe
from trusted_runtime.integration.engine import assemble_execution_decision
from trusted_runtime.review import load_review_input


def test_to_json_safe_normalizes_path_and_nested_containers():
    payload = {
        "path": Path("example") / "child",
        "values": ({"mode": "x"}, {"other": Path("nested")}),
        "set_values": {"a", "b"},
    }

    result = to_json_safe(payload)

    assert result["path"] == str(Path("example") / "child")
    assert isinstance(result["values"], list)
    assert isinstance(result["set_values"], list)
    assert all(isinstance(item, str) for item in result["set_values"])


def test_export_decision_payload_is_machine_readable_for_live_decision():
    case_path = Path(__file__).resolve().parents[1] / "examples" / "ai_agent_shell_access.json"
    decision = assemble_execution_decision(load_review_input(case_path))

    payload = export_decision_payload(decision)

    assert payload["action_id"] == decision.action_id
    assert payload["risk_state"] == decision.risk_state.value
    assert payload["runtime_disposition"] == decision.runtime_disposition.value
    assert isinstance(payload["integration_mode_report"], dict) or payload["integration_mode_report"] is None
    assert isinstance(payload["cer_bundle"], dict)
    assert isinstance(payload["overall_receipt"], dict)

    rendered = json.dumps(payload, indent=2)
    reparsed = json.loads(rendered)
    assert reparsed["action_id"] == decision.action_id
