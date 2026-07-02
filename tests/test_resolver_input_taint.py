from __future__ import annotations

"""Tests for the resolver-input trust boundary.

Proposer-supplied resolver evidence (grants, status overrides, known refs
arriving via the proposed action's own context) is self-certification. The
interim discipline is taint, not trust: every contributing surface must be
named in proposer_supplied_surfaces, must surface as a
RESOLVER_INPUTS_PROPOSER_SUPPLIED soft flag on every verification path, and
must deny a clean PASS. Runtime-observed evidence must NOT taint.
"""

from pathlib import Path

import pytest

from trusted_runtime.config import load_integration_paths
from trusted_runtime.integration.attest_bridge import AttestBridge, AttestResolverInputs
from trusted_runtime.integration.engine import _attest_resolver_inputs_for_action
from trusted_runtime.shared.models import EvidenceRecord, ProposedAction


def _action(context: dict | None = None) -> ProposedAction:
    return ProposedAction(
        id="taint-001",
        description="Run a state-changing operation.",
        context=context or {},
        proposed_by="agent-session",
    )


def _evidence(source: str) -> EvidenceRecord:
    return EvidenceRecord(kind="observation", source=source, content="observed by runtime")


def test_context_supplied_trust_surfaces_are_tainted():
    inputs = _attest_resolver_inputs_for_action(
        _action({
            "attest_known_message_refs": ["msg:claimed"],
            "attest_authority_grants": {"approval:self": {"granted_type": "HUMAN_APPROVAL", "granted_scope": "state_change"}},
            "attest_authority_status_overrides": {"approval:self": "resolved"},
        }),
        [],
    )
    assert sorted(inputs.proposer_supplied_surfaces) == [
        "authority_grants",
        "authority_status_overrides",
        "known_message_refs",
    ]
    assert sorted(inputs.taint_flags()) == [
        "RESOLVER_INPUTS_PROPOSER_SUPPLIED:authority_grants",
        "RESOLVER_INPUTS_PROPOSER_SUPPLIED:authority_status_overrides",
        "RESOLVER_INPUTS_PROPOSER_SUPPLIED:known_message_refs",
    ]


def test_runtime_observed_evidence_does_not_taint():
    inputs = _attest_resolver_inputs_for_action(_action(), [_evidence("msg:runtime-observed")])
    assert "msg:runtime-observed" in inputs.known_message_refs
    assert inputs.proposer_supplied_surfaces == []
    assert inputs.taint_flags() == []


def test_empty_context_surfaces_do_not_taint():
    inputs = _attest_resolver_inputs_for_action(
        _action({"attest_known_message_refs": [], "attest_authority_grants": {}}),
        [],
    )
    assert inputs.proposer_supplied_surfaces == []


def test_stub_path_carries_taint_flags(tmp_path: Path):
    bridge = AttestBridge(attest_root=tmp_path / "definitely-absent")
    tainted = AttestResolverInputs(
        authority_status_overrides={"approval:self": "resolved"},
        proposer_supplied_surfaces=["authority_status_overrides"],
    )
    msg = bridge.wrap_adapter_assert(
        layer_name="council", content={"finding": "x"}, grounds=["msg:g"], parents=["msg:root"],
    )
    result = bridge.verify_for_runtime(msg, [], resolver_inputs=tainted)
    assert "RESOLVER_INPUTS_PROPOSER_SUPPLIED:authority_status_overrides" in result.soft_flag
    assert result.decision_effect == "UNVERIFIABLE"


def _real_attest_root():
    return load_integration_paths().attest_agent_conlang_src


def test_real_path_taint_denies_clean_pass_differentially():
    root = _real_attest_root()
    if root is None:
        pytest.skip("AttestAgentConlang sibling repo absent; set ATTEST_AGENT_CONLANG_SRC to run the real seam")

    bridge = AttestBridge(attest_root=root)
    assert bridge.real_available is True
    msg = bridge.wrap_ingress_request(_action())

    untainted = bridge.verify_for_runtime(msg, [], resolver_inputs=AttestResolverInputs())
    tainted = bridge.verify_for_runtime(
        msg,
        [],
        resolver_inputs=AttestResolverInputs(
            authority_grants={"approval:self": {"granted_type": "HUMAN_APPROVAL", "granted_scope": "state_change"}},
            proposer_supplied_surfaces=["authority_grants"],
        ),
    )

    for r in (untainted, tainted):
        assert "ATTEST_BRIDGE_DESIGN_STUB_ONLY" not in r.soft_flag
        assert r.verifier_version == "attest_ref_impl"

    assert not any(f.startswith("RESOLVER_INPUTS_PROPOSER_SUPPLIED") for f in untainted.soft_flag)
    assert "RESOLVER_INPUTS_PROPOSER_SUPPLIED:authority_grants" in tainted.soft_flag
    assert tainted.decision_effect != "PASS"
    if untainted.decision_effect == "PASS":
        assert tainted.decision_effect == "REVIEW"
    assert tainted.hard_fail == untainted.hard_fail
