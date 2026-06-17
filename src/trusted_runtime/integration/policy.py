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
    independently_corroborated: bool = True,
    reviewability_exceeded: bool = False,
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
    return runtime_disposition, None
