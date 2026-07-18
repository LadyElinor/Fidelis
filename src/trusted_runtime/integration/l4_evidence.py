from __future__ import annotations

from typing import Any

from trusted_runtime.shared.enums import TripValidationStatus
from trusted_runtime.shared.models import SophronValidation


def build_sophron_validation_envelope(
    *,
    sophron_report_valid: bool,
    sophron_signals: dict[str, Any],
    tas_local_validation: dict[str, Any],
    sophron_report: dict[str, Any],
    sophron_stdout: str,
    l4_closure: dict[str, Any],
    degradation_reason: str | None,
    receipt_linkage: bool,
    tas_closure_referenced: bool,
) -> dict[str, Any]:
    has_partial_sophron_structure = bool(sophron_report) or bool(sophron_signals)

    if sophron_report_valid:
        validation_status = "VALIDATED"
    elif degradation_reason is not None:
        validation_status = "FAILED"
    elif tas_local_validation and has_partial_sophron_structure:
        validation_status = "CALIBRATING"
    elif tas_local_validation:
        validation_status = "UNAVAILABLE"
    else:
        validation_status = "UNAVAILABLE"

    closure_summary = (
        "SOPHRON validation linked to TAS enforcement trace"
        if tas_closure_referenced and receipt_linkage
        else "SOPHRON validation incomplete or only partially linked"
    )

    return SophronValidation(
        validation_status=validation_status,
        signal_tiers=sophron_signals,
        closure_summary=closure_summary,
        degradation_reason=degradation_reason,
        receipt_linkage=receipt_linkage,
        tas_closure_referenced=tas_closure_referenced,
        checkpoint_mode="runtime-derived",
        l4_closure=l4_closure,
        tas_local_validation=tas_local_validation,
        sophron_report=sophron_report,
        sophron_stdout=sophron_stdout,
        passed=sophron_report_valid,
        signals=sophron_signals,
    )
