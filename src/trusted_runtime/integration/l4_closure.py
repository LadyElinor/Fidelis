from __future__ import annotations

from typing import Any


def evaluate_l4_closure(
    *,
    tas_local_validation: dict[str, Any] | None,
    sophron_report: dict[str, Any] | None,
    sophron_report_valid: bool,
    provenance_hashes: list[str],
    state_vectors: list[dict[str, Any]],
    invariants_checked: list[dict[str, Any]],
    adapter_error: str | None = None,
) -> dict[str, Any]:
    checks = {
        "tas_local_validation": bool(tas_local_validation),
        "sophron_report": bool(sophron_report),
        "sophron_report_valid": sophron_report_valid,
        "provenance_hashes": bool(provenance_hashes),
        "state_vectors": bool(state_vectors),
        "invariants_checked": bool(invariants_checked),
    }
    missing = [name for name, ok in checks.items() if not ok]
    return {
        "closure_bar_version": "phase3-v1",
        "closure_requirements": list(checks.keys()),
        "closure_checks": checks,
        "closure_missing": missing,
        "closure_complete": not missing,
        "degradation_reason": adapter_error,
        "reporting_axes": {
            "tas_local_only": bool(tas_local_validation) and not sophron_report_valid,
            "sophron_validated": sophron_report_valid,
            "adapter_failed": adapter_error is not None,
        },
    }
