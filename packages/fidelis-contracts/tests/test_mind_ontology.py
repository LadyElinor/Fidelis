from fidelis_contracts import (
    AdapterProvenance,
    BehavioralObservation,
    MetricObservation,
    MindOntologyCausalSupport,
    MindOntologyInterpretation,
    MindOntologyProbeMode,
    MindOntologyProbeReceipt,
)


def test_behavioral_black_box_receipt_stays_observational_and_serializable() -> None:
    receipt = MindOntologyProbeReceipt(
        probe_id="probe-1",
        probe_mode=MindOntologyProbeMode.BEHAVIORAL_BLACK_BOX,
        model_id="example-model",
        provider="example-provider",
        model_revision="rev-1",
        generator_id="mind-ontology-probe-runner",
        generator_version="0.1.0",
        generated_at="2026-08-05T21:10:00Z",
        reference_population_ids=("human-ref-v1",),
        behavioral_observations=(
            BehavioralObservation(
                prompt_set_digest="sha256:prompts",
                decoding_config_digest="sha256:decode",
                system_prompt_digest="sha256:system",
                summary="Observed a distribution shift under the reference probe.",
                metrics=(
                    MetricObservation(
                        metric="js_divergence",
                        value=0.18,
                        baseline_value=0.11,
                        delta_value=0.07,
                        sign_convention="higher_means_farther_from_reference_distribution",
                        reference_population_id="human-ref-v1",
                        reference_dataset_revision="2026-08-04",
                    ),
                ),
            ),
        ),
        negative_control_results=("No corresponding shift on unrelated arithmetic prompts.",),
        interpretation=MindOntologyInterpretation.REFERENCE_PATTERN_OBSERVED,
        causal_support=MindOntologyCausalSupport.OBSERVATIONAL_ONLY,
        limitations=("Single provider revision only.",),
        provenance=AdapterProvenance.NATIVE,
    )

    payload = receipt.to_dict()
    assert payload["probe_mode"] == MindOntologyProbeMode.BEHAVIORAL_BLACK_BOX
    assert payload["interpretation"] == MindOntologyInterpretation.REFERENCE_PATTERN_OBSERVED
    assert payload["causal_support"] == MindOntologyCausalSupport.OBSERVATIONAL_ONLY
    assert payload["generator_id"] == "mind-ontology-probe-runner"
    assert payload["schema_version"] == "mind-ontology-probe-0.1"


def test_behavioral_black_box_receipt_rejects_white_box_observations() -> None:
    try:
        MindOntologyProbeReceipt(
            probe_id="probe-2",
            probe_mode=MindOntologyProbeMode.BEHAVIORAL_BLACK_BOX,
            model_id="example-model",
            geometry_observations=(),
            intervention_observations=(object(),),  # type: ignore[arg-type]
        )
    except ValueError:
        pass
    else:
        raise AssertionError("behavioral receipts should reject intervention observations")
