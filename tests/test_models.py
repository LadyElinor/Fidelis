from datetime import datetime, timezone

from trusted_runtime.integration.engine import assemble_execution_decision, default_adapters
from trusted_runtime.integration.translation import derive_meaning_case_key
from trusted_runtime.shared.enums import AdapterProvenance, DecisionIntegrity, RuntimeDisposition
from trusted_runtime.shared.models import ProposedAction


FIXED_TS = datetime(2026, 6, 11, 18, 0, tzinfo=timezone.utc)


def test_real_council_and_warrant_paths_are_explicit():
    action = ProposedAction(
        id="test-real-001",
        description="Should the agent auto-approve a code change that modifies a safety-critical invariant in OpenClaw core?",
        timestamp=FIXED_TS,
        context={"change_type": "safety_invariant", "risk_context": "recursive self-improvement loop"},
    )
    decision = assemble_execution_decision(action)

    assert decision.council.adapter_provenance is AdapterProvenance.REAL
    assert decision.warrant is not None
    assert decision.warrant.adapter_provenance is AdapterProvenance.REAL
    assert decision.reconciliation is not None
    assert decision.decision_integrity is DecisionIntegrity.PARTIAL
    assert decision.adapter_provenance["cer_bundle"] is AdapterProvenance.STUB


def test_translation_maps_safety_invariant_to_attest():
    case_key, notes = derive_meaning_case_key(
        "Auto-approve a code change that modifies a safety-critical invariant in OpenClaw core.",
        {"change_type": "safety_invariant"},
    )
    assert case_key == "attest"
    assert any("attest" in note for note in notes)


def test_overall_receipt_is_deterministic_for_identical_inputs():
    action = ProposedAction(
        id="test-determinism-001",
        description="Should the agent auto-approve a code change that modifies a safety-critical invariant in OpenClaw core?",
        timestamp=FIXED_TS,
        context={"change_type": "safety_invariant"},
    )
    first = assemble_execution_decision(action)
    second = assemble_execution_decision(action)
    assert first.overall_receipt.sha256 == second.overall_receipt.sha256


def test_unknown_translation_falls_back_to_stub_warrant_explicitly():
    action = ProposedAction(
        id="test-stub-001",
        description="Schedule a routine low-risk maintenance reminder.",
        timestamp=FIXED_TS,
        context={},
    )
    decision = assemble_execution_decision(action)
    assert decision.warrant is not None
    assert decision.warrant.adapter_provenance is AdapterProvenance.STUB
    assert decision.decision_integrity in {DecisionIntegrity.PARTIAL, DecisionIntegrity.DEMO_ONLY}


def test_proceed_is_not_allowed_with_stubbed_required_layers():
    action = ProposedAction(
        id="test-guard-001",
        description="Routine harmless scheduling action.",
        timestamp=FIXED_TS,
        context={},
    )
    decision = assemble_execution_decision(action)
    assert decision.runtime_disposition is not RuntimeDisposition.PROCEED


def test_process_provenance_is_present_for_each_layer():
    action = ProposedAction(
        id="test-prov-001",
        description="Should the agent auto-approve a code change that modifies a safety-critical invariant in OpenClaw core?",
        timestamp=FIXED_TS,
        context={"change_type": "safety_invariant"},
    )
    decision = assemble_execution_decision(action)
    assert set(decision.process_provenance.keys()) == {"council", "warrant", "cer_bundle"}
    assert all("record_sha256" in item for item in decision.process_provenance.values())


def test_default_adapters_construct_cleanly():
    adapters = default_adapters()
    assert adapters.hazard is not None
    assert adapters.warrant is not None
    assert adapters.telemetry is not None
