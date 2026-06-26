from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from trusted_runtime.integration.engine import assemble_execution_decision
from trusted_runtime.integration.report import render_markdown_report
from trusted_runtime.integration.status import adapter_status
from trusted_runtime.review import load_review_input


class LiveStackRequirementError(RuntimeError):
    pass


def run_live_stack_smoke(input_path: Path, output_dir: Path, *, require_all_real: bool = False) -> dict[str, Any]:
    action = load_review_input(input_path)
    status = adapter_status()
    integration_mode = status.get("integration_mode", "unknown")

    if require_all_real and integration_mode != "all-real":
        raise LiveStackRequirementError(
            f"live-stack-smoke requires all-real integration mode, found '{integration_mode}'"
        )

    decision = assemble_execution_decision(action)
    output_dir.mkdir(parents=True, exist_ok=True)

    smoke_artifact = {
        "smoke_test": {
            "case_path": str(input_path),
            "integration_mode": integration_mode,
            "require_all_real": require_all_real,
            "adapter_status": status,
            "adapter_provenance": {k: v.value for k, v in decision.adapter_provenance.items()},
            "independently_corroborated": decision.independently_corroborated,
            "self_attested_evidence_only": decision.self_attested_evidence_only,
            "certification_grade_corroboration": decision.correlation_report.get("certification_grade_corroboration", False),
            "weakest_detector_independence": decision.correlation_report.get("weakest_detector_independence", "unknown"),
            "runtime_disposition": decision.runtime_disposition.value,
            "risk_state": decision.risk_state.value,
            "decision_integrity": decision.decision_integrity.value,
            "fail_closed_reason": None,
        }
    }

    (output_dir / "smoke_decision_output.json").write_text(decision.model_dump_json(indent=2), encoding="utf-8")
    (output_dir / "smoke_decision_report.md").write_text(render_markdown_report(decision), encoding="utf-8")
    (output_dir / "live_stack_smoke.json").write_text(json.dumps(smoke_artifact, indent=2), encoding="utf-8")
    return smoke_artifact
