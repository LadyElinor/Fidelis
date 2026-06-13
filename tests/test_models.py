from datetime import datetime, timezone
from pathlib import Path

from trusted_runtime.integration.availability import (
    ethics_council_available,
    meaning_assay_available,
    real_telemetry_stack_available,
    sophron_cer_available,
    trustworthy_agent_stack_available,
)
from trusted_runtime.integration.engine import assemble_execution_decision, default_adapters
from trusted_runtime.integration.policy import guard_runtime_disposition
from trusted_runtime.integration.translation import derive_meaning_case_key
from trusted_runtime.review import build_pr_review_action, load_review_input
from trusted_runtime.shared.enums import AdapterProvenance, DecisionIntegrity, RuntimeDisposition
from trusted_runtime.shared.models import ProposedAction


FIXED_TS = datetime(2026, 6, 11, 18, 0, tzinfo=timezone.utc)


def test_council_and_warrant_paths_are_explicit_for_current_environment():
    action = ProposedAction(
        id="test-real-001",
        description="Should the agent auto-approve a code change that modifies a safety-critical invariant in OpenClaw core?",
        timestamp=FIXED_TS,
        context={"change_type": "safety_invariant", "risk_context": "recursive self-improvement loop"},
    )
    decision = assemble_execution_decision(action)

    expected_council = AdapterProvenance.REAL if ethics_council_available() else AdapterProvenance.STUB
    expected_warrant = AdapterProvenance.REAL if meaning_assay_available() else AdapterProvenance.STUB

    assert decision.council.adapter_provenance is expected_council
    assert decision.warrant is not None
    assert decision.warrant.adapter_provenance is expected_warrant
    if expected_warrant is AdapterProvenance.REAL:
        assert decision.reconciliation is not None
    expected_tas = AdapterProvenance.REAL if trustworthy_agent_stack_available() else AdapterProvenance.STUB
    assert decision.adapter_provenance["tas"] is expected_tas
    if real_telemetry_stack_available() and decision.cer_bundle.sophron_validation.get("passed") is True:
        assert decision.adapter_provenance["cer_bundle"] is AdapterProvenance.REAL
    else:
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
    assert set(decision.process_provenance.keys()) == {"council", "warrant", "tas", "cer_bundle"}
    assert all("record_sha256" in item for item in decision.process_provenance.values())


def test_default_adapters_construct_cleanly():
    adapters = default_adapters()
    assert adapters.hazard is not None
    assert adapters.warrant is not None
    assert adapters.telemetry is not None


def test_real_telemetry_path_surfaces_sophron_report_when_available():
    action = ProposedAction(
        id="test-telemetry-001",
        description="Review PR change set: Tighten invariant handling",
        timestamp=FIXED_TS,
        context={
            "review_kind": "pull_request",
            "change_type": "safety_invariant",
            "changed_files": ["src/core/invariants.py"],
        },
    )
    decision = assemble_execution_decision(action)
    if sophron_cer_available() and trustworthy_agent_stack_available():
        assert "sophron_report" in decision.cer_bundle.sophron_validation
        if decision.adapter_provenance["cer_bundle"] is AdapterProvenance.REAL:
            assert decision.cer_bundle.sophron_validation["passed"] is True
    else:
        assert decision.adapter_provenance["cer_bundle"] is AdapterProvenance.STUB


def test_under_justified_refuse_cannot_auto_proceed():
    action = ProposedAction(
        id="asi-early-release-policy-001",
        description="Authorize early release of a far-more-capable ASI to address urgent global problems, with control guarantees known to be incomplete.",
        timestamp=FIXED_TS,
        context={
            "meaning_case_key": "early_release",
            "review_kind": "scenario_evaluation",
            "change_type": "safety_invariant",
        },
    )
    decision = assemble_execution_decision(action)
    if decision.decision_integrity is DecisionIntegrity.FULL and decision.reconciliation is not None:
        if decision.reconciliation.warranted_action == "REFUSE" and decision.reconciliation.alignment == "UNDER_JUSTIFIED":
            assert decision.runtime_disposition is not RuntimeDisposition.PROCEED


def test_guard_blocks_overreaction_even_without_refuse():
    disposition, note = guard_runtime_disposition(
        RuntimeDisposition.PROCEED,
        {
            "council": AdapterProvenance.REAL,
            "warrant": AdapterProvenance.REAL,
            "cer_bundle": AdapterProvenance.REAL,
        },
        warranted_action="ALLOW",
        reconciliation_alignment="OVER_REACTION",
    )
    assert disposition is RuntimeDisposition.CONFIRM_HUMAN
    assert note is not None and "over-reactive" in note


def test_guard_blocks_refuse_even_without_under_justified_alignment():
    disposition, note = guard_runtime_disposition(
        RuntimeDisposition.PROCEED,
        {
            "council": AdapterProvenance.REAL,
            "warrant": AdapterProvenance.REAL,
            "cer_bundle": AdapterProvenance.REAL,
        },
        warranted_action="REFUSE",
        reconciliation_alignment="ALIGNED",
    )
    assert disposition is RuntimeDisposition.CONFIRM_HUMAN
    assert note is not None and "adverse" in note


def test_build_pr_review_action_creates_pull_request_context():
    action = build_pr_review_action(
        review_id="review-001",
        title="Tighten invariant handling",
        diff_summary="Changes safety-critical invariant checks in runtime.",
        repo="LadyElinor/OpenClaw",
        pr_number=42,
        author="agent-session",
        changed_files=["src/core/invariants.py"],
        extra_context={"change_type": "safety_invariant"},
    )
    assert action.context["review_kind"] == "pull_request"
    assert action.context["pr_number"] == 42
    assert action.context["change_type"] == "safety_invariant"


def test_load_review_input_reads_sample_json():
    sample = Path(__file__).resolve().parents[1] / "examples" / "sample_pr_review.json"
    action = load_review_input(sample)
    assert action.id == "review-openclaw-pr-42"
    assert action.context["review_kind"] == "pull_request"
    assert action.context["change_type"] == "safety_invariant"
