from __future__ import annotations

from runtime.models import TelemetryVector


def evaluate(vector: TelemetryVector) -> list[str]:
    flags: list[str] = []

    if vector.reversibility < 0.4 and vector.agency_level > 0.7:
        flags.append("irreversible_high_agency_action")
    if vector.consent_quality < 0.5:
        flags.append("weak_consent_quality")
    if vector.independence_score < 0.5:
        flags.append("weak_independence")

    return flags
