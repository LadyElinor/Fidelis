from fidelis_contracts import (
    AdapterProvenance,
    BelarionAssay,
    BlastRadius,
    CandidateStatus,
    ClaimLevel,
    ConstraintAssessment,
    ConstraintType,
    ExposureProfile,
    ProjectionAssessment,
    PromotionRecord,
    ReturnAssessment,
    ReturnStatus,
)


def test_private_symbolic_candidate_remains_distinct_from_public_authority() -> None:
    assay = BelarionAssay(
        decision_id="decision-1",
        candidate_status=CandidateStatus.PRIVATE_USE,
        promotions=(
            PromotionRecord(
                source_level=ClaimLevel.EXPERIENCE,
                target_level=ClaimLevel.SYMBOLIC_ASSOCIATION,
                statement="The image carries personal significance.",
                warranted=True,
                confidence=0.9,
            ),
        ),
        constraint_assessments=(
            ConstraintAssessment(
                constraint="Keep the interpretation private and revisable.",
                constraint_type=ConstraintType.ENABLING,
                capacities_enabled=("reflection", "revision"),
            ),
        ),
        exposure=ExposureProfile(
            affected_parties=("author",),
            self_regarding=True,
            voluntary_for_all=True,
            reversible=True,
            domains=("journal",),
            blast_radius=BlastRadius.PRIVATE,
        ),
        projection=ProjectionAssessment(),
        return_assessment=ReturnAssessment(status=ReturnStatus.NOT_REQUIRED),
        significance_warrant_separated=True,
        private_meaning_promoted_to_public_authority=False,
        recommended_gate="allow_private_use",
        provenance=AdapterProvenance.NATIVE,
    )

    payload = assay.to_dict()
    assert payload["candidate_status"] == CandidateStatus.PRIVATE_USE
    assert payload["private_meaning_promoted_to_public_authority"] is False
    assert payload["schema_version"] == "belarion-0.1"


def test_confidence_and_autonomy_risk_are_bounded() -> None:
    try:
        PromotionRecord(
            source_level=ClaimLevel.OBSERVATION,
            target_level=ClaimLevel.CAUSAL_CLAIM,
            statement="invalid",
            confidence=1.1,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("out-of-range confidence should fail")

    try:
        ProjectionAssessment(autonomy_risk=-0.1)
    except ValueError:
        pass
    else:
        raise AssertionError("out-of-range autonomy risk should fail")
