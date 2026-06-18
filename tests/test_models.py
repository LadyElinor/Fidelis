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
from trusted_runtime.shared.enums import AdapterProvenance, DecisionIntegrity, RuntimeDisposition, TripValidationStatus
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


def test_guard_blocks_proceed_without_independent_corroboration():
    disposition, note = guard_runtime_disposition(
        RuntimeDisposition.PROCEED,
        {
            "council": AdapterProvenance.REAL,
            "warrant": AdapterProvenance.REAL,
            "cer_bundle": AdapterProvenance.REAL,
        },
        independently_corroborated=False,
    )
    assert disposition is RuntimeDisposition.CONFIRM_HUMAN
    assert note is not None and "independent corroboration" in note


def test_guard_allows_proceed_with_independent_corroboration():
    disposition, note = guard_runtime_disposition(
        RuntimeDisposition.PROCEED,
        {
            "council": AdapterProvenance.REAL,
            "warrant": AdapterProvenance.REAL,
            "cer_bundle": AdapterProvenance.REAL,
        },
        independently_corroborated=True,
    )
    assert disposition is RuntimeDisposition.PROCEED
    assert note is None


def test_guard_blocks_reviewability_exceeded_proceed():
    disposition, note = guard_runtime_disposition(
        RuntimeDisposition.PROCEED,
        {
            "council": AdapterProvenance.REAL,
            "warrant": AdapterProvenance.REAL,
            "cer_bundle": AdapterProvenance.REAL,
        },
        reviewability_exceeded=True,
    )
    assert disposition is RuntimeDisposition.CONFIRM_HUMAN
    assert note is not None and "reviewability budget" in note


def test_guard_blocks_proceed_when_blocking_tripwire_is_not_validated():
    disposition, note = guard_runtime_disposition(
        RuntimeDisposition.PROCEED,
        {
            "council": AdapterProvenance.REAL,
            "warrant": AdapterProvenance.REAL,
            "cer_bundle": AdapterProvenance.REAL,
        },
        tripwire_records=[
            {
                "tripwire_id": "tripwire.demo",
                "status": TripValidationStatus.CALIBRATING,
                "allowed_for_blocking": True,
            }
        ],
    )
    assert disposition is RuntimeDisposition.CONFIRM_HUMAN
    assert note is not None and "blocking tripwires" in note


def test_decision_surfaces_evidence_reviewability_and_coverage_fields():
    action = ProposedAction(
        id="test-schema-001",
        description="Routine low-risk release with actor-supplied justification only.",
        timestamp=FIXED_TS,
        context={"change_type": "release"},
        proposed_by="agent-session",
    )
    decision = assemble_execution_decision(action)
    assert decision.evidence_records
    assert decision.reviewability.review_budget_chars == 4000
    assert decision.reviewability.review_surface_chars >= decision.reviewability.rationale_chars
    assert "description" in decision.reviewability.review_surface_components
    assert isinstance(decision.coverage_set, list)
    assert isinstance(decision.coverage_records, list)
    assert isinstance(decision.tripwire_records, list)
    assert any(record.tripwire_id == "tripwire.independent_corroboration" for record in decision.tripwire_records)
    assert isinstance(decision.self_attested_evidence_only, bool)
    assert isinstance(decision.independently_corroborated, bool)


def test_actor_only_action_lacks_independent_corroboration():
    action = ProposedAction(
        id="indep-actor-only-001",
        description="Routine release justified solely by the actor's own description.",
        timestamp=FIXED_TS,
        context={"change_type": "release"},
        proposed_by="agent-session",
    )
    decision = assemble_execution_decision(action)
    assert decision.self_attested_evidence_only is True
    assert decision.independently_corroborated is False


def test_changed_files_manifest_alone_does_not_create_independent_corroboration():
    action = ProposedAction(
        id="indep-changed-files-001",
        description="Release that ships an actor-supplied changed-file manifest.",
        timestamp=FIXED_TS,
        context={"change_type": "release", "changed_files": ["src/core/thing.py"]},
        proposed_by="agent-session",
    )
    decision = assemble_execution_decision(action)
    changed_file_records = [record for record in decision.evidence_records if record.kind == "changed_files_manifest"]
    assert changed_file_records and changed_file_records[0].independence_class == "same-operator"
    assert decision.self_attested_evidence_only is False
    assert decision.independently_corroborated is False
    assert not any(record.kind == "changed_files_manifest_verified_local_shape" for record in decision.evidence_records)


def test_coverage_set_only_claims_real_layers():
    action = ProposedAction(
        id="test-coverage-001",
        description="Routine low-risk release.",
        timestamp=FIXED_TS,
        context={"change_type": "release"},
        proposed_by="agent-session",
    )
    decision = assemble_execution_decision(action)
    for layer in decision.coverage_set:
        if layer in {"council", "warrant", "cer_bundle", "tas"}:
            assert decision.adapter_provenance[layer] is AdapterProvenance.REAL
    for record in decision.coverage_records:
        if record.layer in {"council", "warrant", "cer_bundle", "tas"}:
            assert record.mode == "direct-real"
        if record.layer in {"formation_lens", "reconciliation"}:
            assert record.mode == "derived-advisory"


def test_reviewability_counts_contextual_justification_surface():
    action = ProposedAction(
        id="test-review-surface-001",
        description="Review PR change set: test\n\nDiff summary:\nshort summary",
        timestamp=FIXED_TS,
        context={
            "review_kind": "pull_request",
            "repo": "LadyElinor/TrustedRuntime",
            "author": "agent-session",
            "changed_files": ["src/trusted_runtime/integration/engine.py", "tests/test_models.py"],
        },
        proposed_by="agent-session",
    )
    decision = assemble_execution_decision(action)
    assert decision.reviewability.review_surface_chars > decision.reviewability.rationale_chars
    assert "context.changed_files" in decision.reviewability.review_surface_components
    assert "context.repo" in decision.reviewability.review_surface_components


def test_changed_files_can_be_verified_against_local_trustedruntime_repo_state():
    action = ProposedAction(
        id="test-local-path-verify-001",
        description="Review local TrustedRuntime change set.",
        timestamp=FIXED_TS,
        context={
            "review_kind": "pull_request",
            "repo": "LadyElinor/TrustedRuntime",
            "changed_files": [
                "src/trusted_runtime/integration/engine.py",
                "tests/test_models.py",
            ],
        },
        proposed_by="agent-session",
    )
    decision = assemble_execution_decision(action)
    assert decision.independently_corroborated is True
    assert any(record.kind == "changed_files_manifest_verified_local_existence" for record in decision.evidence_records)


def test_missing_changed_files_are_recorded_when_local_repo_verification_fails():
    action = ProposedAction(
        id="test-local-path-miss-001",
        description="Review local TrustedRuntime change set with missing files.",
        timestamp=FIXED_TS,
        context={
            "review_kind": "pull_request",
            "repo": "LadyElinor/TrustedRuntime",
            "changed_files": ["src/receipts/schema.py"],
        },
        proposed_by="agent-session",
    )
    decision = assemble_execution_decision(action)
    assert decision.independently_corroborated is False
    miss_records = [record for record in decision.evidence_records if record.kind == "changed_files_manifest_missing_local_paths"]
    assert miss_records and miss_records[0].independence_class == "same-operator"


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
