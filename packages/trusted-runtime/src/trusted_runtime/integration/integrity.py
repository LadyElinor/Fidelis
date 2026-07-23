from __future__ import annotations

from trusted_runtime.shared.enums import AdapterProvenance


def classify_decision_integrity(adapter_provenance: dict[str, AdapterProvenance]) -> str:
    values = list(adapter_provenance.values())
    if values and all(item is AdapterProvenance.REAL for item in values):
        return "FULL"
    if any(item is AdapterProvenance.REAL for item in values):
        return "PARTIAL"
    return "DEMO_ONLY"
