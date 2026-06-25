from __future__ import annotations

from trusted_runtime.integration.engine import assemble_execution_decision
from trusted_runtime.shared.enums import AdapterProvenance
from trusted_runtime.shared.models import ProposedAction


def test_general_pull_request_action_uses_real_warrant_adapter():
    decision = assemble_execution_decision(
        ProposedAction(
            id="pr1",
            description="review repo integration governance safety multi-step",
            context={"repo": "TrustedRuntime", "review_kind": "pull_request", "changed_files": ["src/trusted_runtime/integration/engine.py"]},
            proposed_by="op",
        )
    )
    assert decision.warrant is not None
    assert decision.warrant.adapter_provenance is AdapterProvenance.REAL
    assert decision.warrant.pair_contrasts is not None
    assert decision.warrant.pair_contrasts.get("source_case") == "over_refusal"
    assert decision.warrant.pair_contrasts.get("translation_fit_quality") == "medium"


def test_general_nonmatched_action_still_avoids_stub_when_meaning_assay_is_available():
    decision = assemble_execution_decision(
        ProposedAction(
            id="g1",
            description="general governance review task",
            context={},
            proposed_by="op",
        )
    )
    assert decision.warrant is not None
    assert decision.warrant.adapter_provenance is AdapterProvenance.REAL
    assert decision.warrant.pair_contrasts is not None
    assert decision.warrant.pair_contrasts.get("source_case") == "attest"
    assert decision.warrant.pair_contrasts.get("translation_fit_quality") == "fallback"
    assert decision.warrant.pair_contrasts.get("fallback_used") is True


def test_new_case_family_with_local_meaning_case_is_marked_real():
    decision = assemble_execution_decision(
        ProposedAction(
            id="g2",
            description="A hiring model created disparate impact against women applicants",
            context={},
            proposed_by="op",
        )
    )
    assert decision.warrant is not None
    assert decision.warrant.pair_contrasts is not None
    assert decision.warrant.pair_contrasts.get("source_case") == "fairness_disparate_impact"
    assert decision.warrant.pair_contrasts.get("translation_fit_quality") == "high"
    assert decision.warrant.adapter_provenance is AdapterProvenance.REAL
