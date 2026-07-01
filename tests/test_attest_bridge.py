from datetime import datetime, timezone

import pytest

from trusted_runtime.integration.attest_bridge import (
    AttestBridge,
    AttestReviewPacket,
    AttestVerificationState,
    IndependenceSignals,
)
from trusted_runtime.integration.availability import attest_agent_conlang_available
from trusted_runtime.shared.models import ProposedAction


FIXED_TS = datetime(2026, 7, 1, 22, 11, tzinfo=timezone.utc)


def _action() -> ProposedAction:
    return ProposedAction(
        id="attest-bridge-001",
        description="Review a safety-critical invariant change before runtime execution.",
        timestamp=FIXED_TS,
        context={"change_type": "safety_invariant", "review_kind": "pull_request"},
        proposed_by="operator",
    )


def _verification(
    *,
    decision_effect: str = "PASS",
    hard_fail: list[str] | None = None,
    soft_flag: list[str] | None = None,
) -> AttestVerificationState:
    return AttestVerificationState(
        message_id="msg-001",
        canonical_hash="hash-001",
        profile_id="attest-default-v02",
        profile_version="draft",
        profile_hash="profile-hash-001",
        verifier_version="test-verifier",
        hard_fail=hard_fail or [],
        soft_flag=soft_flag or [],
        pass_scope_limit=[],
        decision_effect=decision_effect,
        known_message_set_hash="known-set-hash-001",
        evaluated_at=FIXED_TS,
    )


def test_ingress_wraps_as_request_not_assert():
    bridge = AttestBridge()
    msg = bridge.wrap_ingress_request(_action())

    assert msg["frame"] == "REQUEST"
    assert msg["from"] == "trusted-runtime:ingress"
    assert msg["to"] == "trusted-runtime:orchestrator"
    assert msg["content"]["action_id"] == "attest-bridge-001"


def test_endorse_requires_adopts_and_adoption_reason():
    bridge = AttestBridge()

    with pytest.raises(ValueError, match=r"ENDORSE requires adopts\[\] and adoption_reason"):
        bridge.wrap_endorsement(
            layer_name="warrant",
            content={"claim": "adopt prior assessment"},
            grounds=["msg-a"],
            parents=["msg-parent"],
            adopts=[],
            adoption_reason="",
        )


def test_commit_rejected_for_non_whitelisted_emitter():
    bridge = AttestBridge()

    with pytest.raises(ValueError, match="COMMIT emitter not whitelisted"):
        bridge.wrap_runtime_commit(
            runtime_actor="trusted-runtime:warrant",
            content={"execute": True},
            parents=["msg-parent"],
            action_scope="general",
            deontic={"polarity": "permit"},
        )


def test_verification_stub_is_unverifiable_not_pass():
    bridge = AttestBridge()
    result = bridge.verify_for_runtime({"frame": "ASSERT", "content": {"x": 1}}, [])

    assert result.decision_effect == "UNVERIFIABLE"
    assert result.soft_flag == ["ATTEST_BRIDGE_DESIGN_STUB_ONLY"]
    assert result.hard_fail == []


def test_real_attest_bridge_availability_matches_import_gate():
    bridge = AttestBridge(attest_root=None)
    assert bridge.real_available is False
    assert isinstance(attest_agent_conlang_available(), bool)


def test_real_attest_verification_path_passes_simple_request_when_available(tmp_path):
    repo_root = tmp_path
    shadow = repo_root / "attest_ref_impl.py"
    shadow.write_text(
        """
from pydantic import BaseModel
class DeploymentProfile(BaseModel):
    name: str = 'shadow-profile'
class AttestMessage(BaseModel):
    frame: str
    mode: str
    from_: str
    to: str | None = None
    parents: list[str] = []
    ordering_anchor: tuple[str, int]
    content: dict
    @classmethod
    def model_validate(cls, payload):
        payload = dict(payload)
        payload['from_'] = payload.pop('from')
        return cls(**payload)
    def compute_id(self):
        return 'shadow-msg-id'
class StaticGroundsResolver:
    def __init__(self, known_refs=None):
        self.known_refs = known_refs or set()
class StaticAuthorityResolver:
    def __init__(self, known_refs=None):
        self.known_refs = known_refs or set()
class AcceptAllSignatureVerifier:
    pass
class AttestVerifier:
    def __init__(self, profile=None, grounds_resolver=None, authority_resolver=None, signature_verifier=None):
        self.profile = profile
    def verify(self, msg, adopted_chain=None, known_messages=None):
        return {'hard_fail': [], 'soft_flag': [], 'pass_scope_limit': []}
def load_profile(path=None):
    return DeploymentProfile()
""",
        encoding="utf-8",
    )
    bridge = AttestBridge(attest_root=repo_root)
    result = bridge.verify_for_runtime(
        {
            "frame": "REQUEST",
            "mode": "legible",
            "from": "trusted-runtime:ingress",
            "to": "trusted-runtime:orchestrator",
            "parents": [],
            "ordering_anchor": ["2026-07-01T22:11:00Z", 1],
            "content": {"action_id": "x", "description": "y", "context": {}, "proposed_by": "z"},
        },
        [],
        evaluated_at=FIXED_TS,
    )

    assert bridge.real_available is True
    assert result.decision_effect == "PASS"
    assert result.message_id == "shadow-msg-id"
    assert result.profile_id == "shadow-profile"
    assert result.soft_flag == []


def test_real_attest_verification_falls_back_truthfully_when_real_path_throws(tmp_path):
    repo_root = tmp_path
    shadow = repo_root / "attest_ref_impl.py"
    shadow.write_text(
        """
class AttestMessage:
    @classmethod
    def model_validate(cls, payload):
        return cls()
    def compute_id(self):
        return 'unused'
class StaticGroundsResolver:
    def __init__(self, known_refs=None):
        pass
class StaticAuthorityResolver:
    def __init__(self, known_refs=None):
        pass
class AcceptAllSignatureVerifier:
    pass
class AttestVerifier:
    def __init__(self, profile=None, grounds_resolver=None, authority_resolver=None, signature_verifier=None):
        pass
    def verify(self, msg, adopted_chain=None, known_messages=None):
        return {'hard_fail': [], 'soft_flag': [], 'pass_scope_limit': []}
def load_profile(path=None):
    raise RuntimeError('broken profile load')
""",
        encoding="utf-8",
    )
    bridge = AttestBridge(attest_root=repo_root)
    result = bridge.verify_for_runtime(
        {
            "frame": "REQUEST",
            "mode": "legible",
            "from": "trusted-runtime:ingress",
            "to": "trusted-runtime:orchestrator",
            "parents": [],
            "ordering_anchor": ["2026-07-01T22:11:00Z", 1],
            "content": {"action_id": "x", "description": "y", "context": {}, "proposed_by": "z"},
        },
        [],
        evaluated_at=FIXED_TS,
    )

    assert bridge.real_available is True
    assert result.decision_effect == "UNVERIFIABLE"
    assert "ATTEST_BRIDGE_DESIGN_STUB_ONLY" in result.soft_flag
    assert any(flag.startswith("ATTEST_REAL_PATH_FAILED:") for flag in result.soft_flag)


def test_shared_grounds_reduce_independence():
    bridge = AttestBridge()
    candidate = {
        "frame": "ASSERT",
        "parents": ["msg-root"],
        "warrant": {"grounds": ["src:file-a", "msg-support-1"]},
    }
    peer = {
        "frame": "ASSERT",
        "parents": ["msg-other"],
        "warrant": {"grounds": ["src:file-a", "msg-support-2"]},
    }

    result = bridge.compute_independence(candidate_message=candidate, peer_messages=[peer])

    assert result.policy_result == "correlated"
    assert "shared_grounds" in result.overlap_reasons
    assert result.shared_external_sources == ["src:file-a"]


def test_same_operator_prevents_independent_corroboration():
    bridge = AttestBridge()
    candidate = {"frame": "ASSERT", "parents": [], "warrant": {"grounds": ["msg-a"]}}
    peer = {"frame": "ASSERT", "parents": [], "warrant": {"grounds": ["msg-b"]}}

    result = bridge.compute_independence(
        candidate_message=candidate,
        peer_messages=[peer],
        candidate_operator="operator-1",
        peer_operators=["operator-1"],
    )

    assert result.policy_result == "same-origin"
    assert result.same_operator is True
    assert result.independence_score == 0.0


def test_unresolved_dissent_ids_preserved_without_retract():
    bridge = AttestBridge()
    packet = AttestReviewPacket(
        layer_name="council",
        frame="DISSENT",
        message_id="dissent-001",
        verification=_verification(decision_effect="REVIEW"),
    )

    assert bridge.unresolved_dissent_ids([packet]) == ["dissent-001"]


def test_cer_receipt_fragment_includes_profile_and_known_message_hash():
    bridge = AttestBridge()
    verification = _verification()
    independence = IndependenceSignals(
        shared_grounds=["src:file-a"],
        overlap_reasons=["shared_grounds"],
        independence_score=0.35,
        policy_result="correlated",
    )

    fragment = bridge.cer_receipt_fragment(verification=verification, independence=independence)

    assert fragment["attest_message_id"] == "msg-001"
    assert fragment["attest_profile_id"] == "attest-default-v02"
    assert fragment["attest_known_message_set_hash"] == "known-set-hash-001"
    assert fragment["attest_decision_effect"] == "PASS"
    assert fragment["attest_independence"]["policy_result"] == "correlated"


def test_verified_but_same_origin_message_still_requires_review():
    bridge = AttestBridge()
    verification = _verification(decision_effect="PASS")
    independence = IndependenceSignals(policy_result="same-origin", independence_score=0.0, same_operator=True)

    assert bridge.decision_effect(verification, independence) == "REVIEW"


def test_hard_fail_maps_to_block():
    bridge = AttestBridge()
    verification = _verification(decision_effect="PASS", hard_fail=["INVALID_WARRANT"])

    assert bridge.decision_effect(verification) == "BLOCK"


def test_soft_flag_maps_to_review_when_no_hard_fail():
    bridge = AttestBridge()
    verification = _verification(decision_effect="PASS", soft_flag=["CONFIDENCE_DOWNGRADED_TO_ASSUMED"])

    assert bridge.decision_effect(verification) == "REVIEW"
