from __future__ import annotations

from runtime.models import CaseInput, LensResult, MeaningAssayResult, TelemetryVector


def compute(case: CaseInput, lens_results: list[LensResult], meaning: MeaningAssayResult) -> TelemetryVector:
    reversibility = {"full": 1.0, "partial": 0.4, "none": 0.1}[case.context.reversible]
    execution_pressure = {"low": 0.2, "medium": 0.7, "high": 0.9}[case.context.deployment_pressure]
    consent_quality = 0.4 if case.authority.authorization_basis == "unclear" else 0.8
    evidence_quality = 0.55 if case.context.claimed_anonymized else 0.4
    affected_parties = 0.76 if case.context.data_contains_personal_information else 0.2
    dissent_present = any(item.verdict == "object" for item in lens_results)

    return TelemetryVector(
        agency_level=meaning.significance,
        reversibility=reversibility,
        affected_parties=affected_parties,
        evidence_quality=evidence_quality,
        consent_quality=consent_quality,
        independence_score=0.8,
        dissent_present=dissent_present,
        execution_pressure=execution_pressure,
    )
