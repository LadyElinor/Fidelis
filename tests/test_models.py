from datetime import datetime, timezone

from trusted_runtime.integration.engine import assemble_execution_decision
from trusted_runtime.shared.enums import AdapterProvenance, NormativeSummary, RiskState, RuntimeDisposition
from trusted_runtime.shared.models import ProposedAction


def test_real_meaning_assay_path_is_explicit_when_available():
    action = ProposedAction(
        id="test-real-001",
        description="Test action",
        timestamp=datetime(2026, 6, 11, 18, 0, tzinfo=timezone.utc),
        context={"meaning_case_key": "attest"},
    )
    decision = assemble_execution_decision(action)

    assert decision.action_id == "test-real-001"
    assert decision.runtime_disposition is RuntimeDisposition.HALT
    assert decision.risk_state is RiskState.RED
    assert decision.normative_summary is NormativeSummary.DANGEROUS
    assert decision.council.adapter_provenance is AdapterProvenance.STUB
    assert decision.cer_bundle.adapter_provenance is AdapterProvenance.STUB
    assert decision.warrant is not None
    assert decision.warrant.adapter_provenance in {AdapterProvenance.REAL, AdapterProvenance.STUB}
    assert decision.adapter_provenance["warrant"] == decision.warrant.adapter_provenance
    assert decision.council.receipt.sha256
    assert decision.cer_bundle.receipt.sha256
    assert decision.overall_receipt.sha256


def test_stub_meaning_assay_path_is_explicit_when_unmapped():
    action = ProposedAction(
        id="test-stub-001",
        description="Unmapped action",
        timestamp=datetime(2026, 6, 11, 18, 0, tzinfo=timezone.utc),
        context={},
    )
    decision = assemble_execution_decision(action)

    assert decision.warrant is not None
    assert decision.warrant.adapter_provenance is AdapterProvenance.STUB
    assert decision.adapter_provenance["warrant"] is AdapterProvenance.STUB
    assert any("stubbed or unavailable" in item.lower() for item in decision.unresolved_questions)


def test_overall_receipt_is_deterministic_for_identical_inputs():
    action = ProposedAction(
        id="test-determinism-001",
        description="Determinism check",
        timestamp=datetime(2026, 6, 11, 18, 0, tzinfo=timezone.utc),
        context={"meaning_case_key": "attest"},
    )
    first = assemble_execution_decision(action)
    second = assemble_execution_decision(action)

    assert first.overall_receipt.sha256 == second.overall_receipt.sha256
