#!/usr/bin/env python3
"""Improved end-to-end demo for TrustworthyAgentStack."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    from .cer_emitter import CerEmitter, ConfirmationProvider
    from .mock_ethics_council import MockEthicsCouncil, hazard_to_required_gates
except ImportError:  # pragma: no cover
    from cer_emitter import CerEmitter, ConfirmationProvider
    from mock_ethics_council import MockEthicsCouncil, hazard_to_required_gates


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_demo(output_dir: Optional[str] = None, approve_confirmation: bool = True) -> Optional[str]:
    print("=== TrustworthyAgentStack End-to-End Demo ===\n")
    output_path = None
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    ethics = MockEthicsCouncil()
    emitter = CerEmitter(confirmation_provider=ConfirmationProvider(approve_confirmation))

    run_id = emitter.start_run("demo_claude_agent")
    step_id = "step_001"

    hazard = ethics.evaluate_action("Write sensitive configuration to external filesystem", risk_level="high")
    emitter.log_hazard_map(hazard.to_payload())

    gates = hazard_to_required_gates(hazard)
    for gate, decision in gates.items():
        justification = f"Decision derived from EthicsCouncil recommendation: {hazard.recommendation}"
        if decision == "pass":
            justification = f"{gate} passed under minimal demo policy"
        emitter.log_mcp_gate_check(step_id=step_id, gate=gate, decision=decision, justification=justification, confidence=0.9)

    candidate_payload = {
        "candidate_id": "cand_0001",
        "step_id": step_id,
        "claim_type": "policy_violation",
        "summary": "Sensitive external write requires verification before execution.",
        "evidence_ref": "hazard_map:hm_0001",
        "producer": "mock_ethics_council",
        "reproduction_hint": "Re-evaluate proposed external write under clean verifier context.",
        "created_at": _now_iso(),
    }
    emitter._append("candidate_find", candidate_payload)

    verification_payload = {
        "verification_id": "ver_0001",
        "candidate_id": "cand_0001",
        "step_id": step_id,
        "verifier": "minimal_verifier",
        "input_artifact_ref": "hazard_map:hm_0001",
        "verification_mode": "review",
        "created_at": _now_iso(),
    }
    emitter._append("independent_verification", verification_payload)

    verification_result_payload = {
        "verification_result_id": "vres_0001",
        "verification_id": "ver_0001",
        "candidate_id": "cand_0001",
        "step_id": step_id,
        "result": "confirmed",
        "confidence": 0.9,
        "summary": "Independent verifier confirms confirmation-gated handling is required.",
        "artifact_ref": "verification:ver_0001",
        "created_at": _now_iso(),
    }
    emitter._append("verification_result", verification_result_payload)

    if any(decision == "escalate" for decision in gates.values()):
        confirmed = emitter.request_confirmation(
            step_id=step_id,
            scope="external_action",
            reason="High-risk or irreversible action requires explicit approval",
            requested_by_gate="consent_traceability",
            requested_action="write_file",
            requested_target="external_filesystem",
        )
        if not confirmed:
            emitter.log_external_action(step_id=step_id, action="write_file", target="external_filesystem", status="blocked")
            print("[CER] Action blocked due to missing confirmation.")
            if output_dir:
                output_path = str(Path(output_dir) / f"demo_export_{run_id}.jsonl")
            return emitter.export_for_sophron(output_path)

    emitter.log_external_action(step_id=step_id, action="write_file", target="external_filesystem", status="simulated")

    if output_dir:
        output_path = str(Path(output_dir) / f"demo_export_{run_id}.jsonl")
    export_path = emitter.export_for_sophron(output_path)
    print("\nDemo completed successfully.")
    print(f"Run ID: {run_id}")
    print(f"Export: {export_path}")
    return export_path


if __name__ == "__main__":
    run_demo()
