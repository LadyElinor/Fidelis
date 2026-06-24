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
