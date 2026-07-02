from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from trusted_runtime.integration.engine import assemble_execution_decision
from trusted_runtime.integration.report import render_markdown_report
from trusted_runtime.integration.status import adapter_status
from trusted_runtime.review import load_review_input
from trusted_runtime.shared.enums import AdapterProvenance, RuntimeDisposition
from trusted_runtime.shared.models import ExecutionDecision, SophronValidation


class LiveStackRequirementError(RuntimeError):
    pass


def _phase4_truthfulness_failures(decision: ExecutionDecision) -> list[str]:
    failures: list[str] = []

    if decision.integration_mode_report is None:
        failures.append("missing computed integration_mode_report")
    if not isinstance(decision.cer_bundle.sophron_validation, SophronValidation):
        failures.append("sophron_validation is not typed SophronValidation")
    else:
        soph = decision.cer_bundle.sophron_validation
        if soph.validation_status not in {"VALIDATED", "CALIBRATING", "FAILED", "UNAVAILABLE"}:
            failures.append(f"unexpected sophron validation status: {soph.validation_status}")
        for signal_id, payload in soph.signal_tiers.items():
            if not signal_id.startswith("sophron."):
                failures.append(f"signal tier missing sophron namespace: {signal_id}")
            if payload.get("signal_id") != signal_id:
                failures.append(f"signal tier id mismatch: {signal_id}")
            if payload.get("source_layer") != "sophron-cer":
                failures.append(f"signal tier wrong source layer: {signal_id}")
            semantic_checks = payload.get("semantic_checks", {}) if isinstance(payload, dict) else {}
            if semantic_checks.get("has_signal_id") is not True:
                failures.append(f"signal tier missing semantic has_signal_id check: {signal_id}")
            if semantic_checks.get("allowed_source_layer") is not True:
                failures.append(f"signal tier failed allowed_source_layer check: {signal_id}")
            if semantic_checks.get("allowed_tier_source") is not True:
                failures.append(f"signal tier failed allowed_tier_source check: {signal_id}")

    if decision.integration_mode_report is not None:
        sophron_mode = decision.integration_mode_report.components.get("sophron_cer")
        if sophron_mode is not None and not sophron_mode.behavior_real and decision.adapter_provenance.get("cer_bundle") is AdapterProvenance.REAL:
            failures.append("cer_bundle claims REAL while sophron_cer behavior_real is false")

    l2_complete = decision.vita_state.get("tas_closure", {}).get("closure_bar", {}).get("closure_complete", False)
    if not l2_complete and decision.runtime_disposition is RuntimeDisposition.PROCEED:
        failures.append("runtime disposition PROCEED despite incomplete L2 closure")

    return failures


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

    computed_mode = decision.integration_mode_report.mode.value if decision.integration_mode_report is not None else integration_mode
    truthfulness_failures = _phase4_truthfulness_failures(decision)
    smoke_artifact = {
        "smoke_test": {
            "case_path": str(input_path),
            "integration_mode": computed_mode,
            "integration_mode_report": json.loads(json.dumps(asdict(decision.integration_mode_report), default=str)) if decision.integration_mode_report is not None else None,
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
            "truthfulness_gate_passed": not truthfulness_failures,
            "phase4_truthfulness_failures": truthfulness_failures,
            "fail_closed_reason": "; ".join(truthfulness_failures) if truthfulness_failures else None,
        }
    }

    (output_dir / "smoke_decision_output.json").write_text(decision.model_dump_json(indent=2), encoding="utf-8")
    (output_dir / "smoke_decision_report.md").write_text(render_markdown_report(decision), encoding="utf-8")
    (output_dir / "live_stack_smoke.json").write_text(json.dumps(smoke_artifact, indent=2), encoding="utf-8")

    if truthfulness_failures:
        raise LiveStackRequirementError(f"phase4 truthfulness regression: {'; '.join(truthfulness_failures)}")

    return smoke_artifact
