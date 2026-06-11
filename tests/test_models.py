from trusted_runtime.integration.engine import assemble_execution_decision
from trusted_runtime.shared.enums import NormativeSummary, RiskState, RuntimeDisposition
from trusted_runtime.shared.models import ProposedAction


def test_golden_pipeline_produces_expected_contract_shape():
    action = ProposedAction(
        id="test-001",
        description="Test action",
        context={"meaning_case_key": "attest"},
    )
    decision = assemble_execution_decision(action)

    assert decision.action_id == "test-001"
    assert decision.runtime_disposition is RuntimeDisposition.HALT
    assert decision.risk_state is RiskState.RED
    assert decision.normative_summary is NormativeSummary.DANGEROUS
    assert decision.council.receipt.sha256
    assert decision.cer_bundle.receipt.sha256
    assert decision.overall_receipt.sha256
    assert decision.warrant is not None
    assert "attest" == decision.warrant.pair_contrasts["source_case"]
    assert any("Real meaning-assay adapter used" in note for note in decision.warrant.confidence_notes)
