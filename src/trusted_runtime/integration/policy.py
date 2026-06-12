from __future__ import annotations

from trusted_runtime.shared.enums import AdapterProvenance, RuntimeDisposition


REQUIRED_REAL_FOR_PROCEED = ("council", "warrant", "cer_bundle")


def proceed_allowed(adapter_provenance: dict[str, AdapterProvenance]) -> bool:
    return all(adapter_provenance.get(key) is AdapterProvenance.REAL for key in REQUIRED_REAL_FOR_PROCEED)


def guard_runtime_disposition(
    runtime_disposition: RuntimeDisposition,
    adapter_provenance: dict[str, AdapterProvenance],
    *,
    warranted_action: str | None = None,
    reconciliation_alignment: str | None = None,
) -> tuple[RuntimeDisposition, str | None]:
    if runtime_disposition is RuntimeDisposition.PROCEED and not proceed_allowed(adapter_provenance):
        return (
            RuntimeDisposition.CONFIRM_HUMAN,
            "PROCEED forbidden while required layers remain stubbed or unavailable",
        )
    if (
        runtime_disposition is RuntimeDisposition.PROCEED
        and warranted_action == "REFUSE"
        and reconciliation_alignment in {"UNDER_JUSTIFIED", "OVER_REACTION"}
    ):
        return (
            RuntimeDisposition.CONFIRM_HUMAN,
            "PROCEED forbidden when warrant reconciliation marks the act as under-justified or over-reactive",
        )
    return runtime_disposition, None
