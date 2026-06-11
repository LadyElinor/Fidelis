"""Bundled worked cases. Each reproduces an analysis we performed by hand."""

from __future__ import annotations

from ..model import Case
from . import attest, kor, scenarios, trinity

REGISTRY: dict[str, Case] = {
    attest.CASE.key: attest.CASE,
    kor.CASE.key: kor.CASE,
    trinity.CASE.key: trinity.CASE,
    scenarios.DB_WIPE.key: scenarios.DB_WIPE,
    scenarios.OVER_REFUSAL.key: scenarios.OVER_REFUSAL,
    scenarios.SILENT_POLICY_WEAKEN.key: scenarios.SILENT_POLICY_WEAKEN,
}


def get(key: str) -> Case:
    if key not in REGISTRY:
        raise KeyError(f"unknown case '{key}'; available: {sorted(REGISTRY)}")
    return REGISTRY[key]
