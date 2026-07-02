from __future__ import annotations

from typing import Any


def evaluate_l2_closure(
    *,
    has_live_stack: bool,
    route_name: str | None,
    gate_records: list[dict[str, Any]],
    evidence_chain: list[str],
    risk_state: str,
    runtime_disposition: str,
    hazard_payload: dict[str, Any] | None,
    receipt_linkage: dict[str, Any] | None = None,
    checkpoints: list[str] | None = None,
) -> dict[str, Any]:
    derived_checkpoints = checkpoints or [
        "observe",
        "route",
        "gate",
        "disposition",
        "receipt",
        "review",
    ]
    checks = {
        "tas_live_stack": has_live_stack,
        "task_route": route_name is not None,
        "gate_decisions": bool(gate_records),
        "gate_coverage_has_task_route": any(record.get("gate") == "task_route" for record in gate_records),
        "evidence_chain": bool(evidence_chain),
        "risk_state_binding": risk_state in {"GREEN", "AMBER", "RED", "BLACK"},
        "runtime_disposition_binding": runtime_disposition in {"PROCEED", "CONFIRM_HUMAN", "HALT", "SUSPEND"},
        "hazard_payload": bool(hazard_payload),
        "receipt_linkage": bool(receipt_linkage and receipt_linkage.get("trace_id") and receipt_linkage.get("source")),
        "checkpoints": len(derived_checkpoints) >= 4,
    }
    missing = [name for name, ok in checks.items() if not ok]
    return {
        "closure_bar_version": "phase2-v3",
        "closure_requirements": list(checks.keys()),
        "closure_checks": checks,
        "closure_missing": missing,
        "closure_complete": not missing,
        "enforcement_trace": {
            "trace_id": receipt_linkage.get("trace_id") if receipt_linkage else None,
            "source": receipt_linkage.get("source") if receipt_linkage else None,
            "checkpoints": derived_checkpoints,
            "checkpoint_mode": "runtime-derived",
        },
    }
