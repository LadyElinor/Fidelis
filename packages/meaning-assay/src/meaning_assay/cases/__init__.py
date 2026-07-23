"""Bundled worked cases. Each reproduces an analysis we performed by hand."""

from __future__ import annotations

from ..model import Case
from . import attest, early_release, kor, kor_dark, scenarios, trinity

REGISTRY: dict[str, Case] = {
    attest.CASE.key: attest.CASE,
    early_release.CASE.key: early_release.CASE,
    kor_dark.CASE.key: kor_dark.CASE,
    kor.CASE.key: kor.CASE,
    trinity.CASE.key: trinity.CASE,
    scenarios.DB_WIPE.key: scenarios.DB_WIPE,
    scenarios.OVER_REFUSAL.key: scenarios.OVER_REFUSAL,
    scenarios.SILENT_POLICY_WEAKEN.key: scenarios.SILENT_POLICY_WEAKEN,
    scenarios.FAIRNESS_DISPARATE_IMPACT.key: scenarios.FAIRNESS_DISPARATE_IMPACT,
    scenarios.OPACITY_UNVERIFIABLE_PERFORMANCE.key: scenarios.OPACITY_UNVERIFIABLE_PERFORMANCE,
    scenarios.INCENTIVE_GAMING_METRIC_CORRUPTION.key: scenarios.INCENTIVE_GAMING_METRIC_CORRUPTION,
    scenarios.PUBLIC_INTEREST_DISCLOSURE_WHISTLEBLOWING.key: scenarios.PUBLIC_INTEREST_DISCLOSURE_WHISTLEBLOWING,
    scenarios.CONCEALMENT_LOSS_ESCALATION.key: scenarios.CONCEALMENT_LOSS_ESCALATION,
    scenarios.ADVERSARIAL_EXPOSURE_WITHOUT_HARDENING.key: scenarios.ADVERSARIAL_EXPOSURE_WITHOUT_HARDENING,
    scenarios.RECORD_CORRECTION_RETRACTION_UNDER_UNCERTAINTY.key: scenarios.RECORD_CORRECTION_RETRACTION_UNDER_UNCERTAINTY,
    scenarios.DISTRIBUTED_ACCOUNTABILITY_SYSTEM_HARM.key: scenarios.DISTRIBUTED_ACCOUNTABILITY_SYSTEM_HARM,
}


def get(key: str) -> Case:
    if key not in REGISTRY:
        raise KeyError(f"unknown case '{key}'; available: {sorted(REGISTRY)}")
    return REGISTRY[key]
