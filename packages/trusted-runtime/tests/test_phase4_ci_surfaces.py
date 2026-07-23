from __future__ import annotations

from datetime import datetime, timezone

from trusted_runtime.integration.engine import assemble_execution_decision
from trusted_runtime.shared.enums import AdapterProvenance, RuntimeDisposition
from trusted_runtime.shared.models import ProposedAction, SophronValidation


FIXED_TS = datetime(2026, 7, 2, 2, 5, tzinfo=timezone.utc)


def _action() -> ProposedAction:
    return ProposedAction(
        id="phase4-ci-001",
        description="Review repo integration governance safety multi-step",
        timestamp=FIXED_TS,
        context={"change_type": "safety_invariant", "review_kind": "pull_request"},
        proposed_by="op",
    )


def test_phase4_decision_carries_mode_report_and_typed_sophron_validation():
    decision = assemble_execution_decision(_action())
    assert decision.integration_mode_report is not None
    assert "sophron_cer" in decision.integration_mode_report.components
    assert isinstance(decision.cer_bundle.sophron_validation, SophronValidation)
    assert decision.cer_bundle.sophron_validation.validation_status in {"VALIDATED", "CALIBRATING", "FAILED", "UNAVAILABLE"}


def test_phase4_no_fake_real_when_mode_is_not_behavior_real():
    decision = assemble_execution_decision(_action())
    sophron_mode = decision.integration_mode_report.components["sophron_cer"]
    if not sophron_mode.behavior_real:
        assert decision.adapter_provenance["cer_bundle"] is not AdapterProvenance.REAL



def test_phase4_l2_l4_closure_truthfulness_blocks_proceed_when_l2_incomplete():
    decision = assemble_execution_decision(_action())
    tas_closure = decision.vita_state.get("tas_closure", {})
    l2_complete = tas_closure.get("closure_bar", {}).get("closure_complete", False)
    if not l2_complete:
        assert decision.runtime_disposition is not RuntimeDisposition.PROCEED



def test_phase4_signal_tiers_are_semantically_checked_when_present():
    decision = assemble_execution_decision(_action())
    signal_tiers = decision.cer_bundle.sophron_validation.signal_tiers
    for signal_id, payload in signal_tiers.items():
        assert signal_id.startswith("sophron.")
        assert payload.get("signal_id") == signal_id
        assert payload.get("source_layer") == "sophron-cer"
        assert payload.get("semantic_checks", {}).get("has_signal_id") is True
        assert payload.get("semantic_checks", {}).get("allowed_source_layer") is True
        assert payload.get("semantic_checks", {}).get("allowed_tier_source") is True
