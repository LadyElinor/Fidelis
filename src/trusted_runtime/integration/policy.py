from __future__ import annotations

from trusted_runtime.shared.enums import AdapterProvenance, RuntimeDisposition, TripValidationStatus


REQUIRED_REAL_FOR_PROCEED = ("council", "warrant", "cer_bundle")


def proceed_allowed(adapter_provenance: dict[str, AdapterProvenance]) -> bool:
    return all(adapter_provenance.get(key) is AdapterProvenance.REAL for key in REQUIRED_REAL_FOR_PROCEED)


def validated_tripwire_blocking_allowed(tripwire_records: list[dict] | list[object] | None) -> bool:
    if not tripwire_records:
        return True
    blocking_records = [record for record in tripwire_records if getattr(record, "allowed_for_blocking", False) or (isinstance(record, dict) and record.get("allowed_for_blocking"))]
    if not blocking_records:
        return True
    for record in blocking_records:
        status = getattr(record, "status", None)
        if status is None and isinstance(record, dict):
            status = record.get("status")
        if status != TripValidationStatus.VALIDATED:
            return False
    return True


def guard_runtime_disposition(
    runtime_disposition: RuntimeDisposition,
    adapter_provenance: dict[str, AdapterProvenance],
    *,
    warranted_action: str | None = None,
    reconciliation_alignment: str | None = None,
    independently_corroborated: bool = True,
    reviewability_exceeded: bool = False,
    tripwire_records: list[dict] | list[object] | None = None,
) -> tuple[RuntimeDisposition, str | None]:
    if runtime_disposition is RuntimeDisposition.PROCEED and not proceed_allowed(adapter_provenance):
        return (
            RuntimeDisposition.CONFIRM_HUMAN,
            "PROCEED forbidden while required layers remain stubbed or unavailable",
        )
    if runtime_disposition is RuntimeDisposition.PROCEED and (
        warranted_action == "REFUSE"
        or reconciliation_alignment in {"UNDER_JUSTIFIED", "OVER_REACTION"}
    ):
        return (
            RuntimeDisposition.CONFIRM_HUMAN,
            "PROCEED forbidden when warrant reconciliation marks the act as adverse or over-reactive",
        )
    if runtime_disposition is RuntimeDisposition.PROCEED and not independently_corroborated:
        return (
            RuntimeDisposition.CONFIRM_HUMAN,
            "PROCEED forbidden without independent corroboration; self-attested and same-operator evidence do not count",
        )
    if runtime_disposition is RuntimeDisposition.PROCEED and reviewability_exceeded:
        return (
            RuntimeDisposition.CONFIRM_HUMAN,
            "PROCEED forbidden when justification exceeds reviewability budget",
        )
    if runtime_disposition is RuntimeDisposition.PROCEED and not validated_tripwire_blocking_allowed(tripwire_records):
        return (
            RuntimeDisposition.CONFIRM_HUMAN,
            "PROCEED forbidden when blocking tripwires are unvalidated, calibrating, or retired",
        )
    return runtime_disposition, None
