from datetime import datetime, timezone

import pytest

from trusted_runtime.integration.attest_bridge import (
    AttestBridge,
    AttestBridgeConfig,
    AttestResolverInputs,
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


def _valid_commit_deontic(**overrides):
    base = {
        "type": "HUMAN_APPROVAL",
        "authority": ["approval:ops-9"],
        "scope": "state_change",
        "binds": {"message": "msg-core-001", "parents": ["msg-parent"]},
        "nonce": "n-1",
    }
    base.update(overrides)
    return base


def test_commit_rejected_for_non_whitelisted_emitter():
    bridge = AttestBridge()

    with pytest.raises(ValueError, match="COMMIT emitter not whitelisted"):
        bridge.wrap_runtime_commit(
            runtime_actor="trusted-runtime:warrant",
            content={"execute": True},
            parents=["msg-parent"],
            action_scope="general",
            deontic=_valid_commit_deontic(scope="general"),
        )


@pytest.mark.parametrize(
    ("deontic", "message"),
    [
        ({"authority": ["approval:ops-9"], "scope": "state_change", "binds": {"message": "m", "parents": ["msg-parent"]}}, "COMMIT deontic requires non-empty type"),
        ({"type": "HUMAN_APPROVAL", "authority": [], "scope": "state_change", "binds": {"message": "m", "parents": ["msg-parent"]}}, "COMMIT deontic requires non-empty authority"),
        ({"type": "HUMAN_APPROVAL", "authority": ["approval:ops-9"], "binds": {"message": "m", "parents": ["msg-parent"]}}, "COMMIT deontic requires non-empty scope"),
        ({"type": "HUMAN_APPROVAL", "authority": ["approval:ops-9"], "scope": "state_change", "binds": {"parents": ["msg-parent"]}}, "COMMIT deontic requires binds.message"),
        ({"type": "HUMAN_APPROVAL", "authority": ["approval:ops-9"], "scope": "state_change", "binds": {"message": "m"}}, "COMMIT deontic requires binds.parents"),
    ],
)
def test_commit_rejected_for_malformed_deontic_payloads(deontic, message):
    bridge = AttestBridge()

    with pytest.raises(ValueError, match=message):
        bridge.wrap_runtime_commit(
            runtime_actor="trusted-runtime:orchestrator",
            content={"execute": True},
            parents=["msg-parent"],
            action_scope="state_change",
            deontic=deontic,
        )


@pytest.mark.parametrize("action_scope", ["general", "state_change", "package_install", "shell_exec", "network_fetch"])
def test_commit_rejected_for_none_deontic_type(action_scope):
    bridge = AttestBridge()

    with pytest.raises(ValueError, match="COMMIT deontic type NONE is invalid for runtime commits"):
        bridge.wrap_runtime_commit(
            runtime_actor="trusted-runtime:orchestrator",
            content={"execute": True},
            parents=["msg-parent"],
            action_scope=action_scope,
            deontic=_valid_commit_deontic(type="NONE", scope=action_scope),
        )


def test_commit_rejected_for_scope_mismatch():
    bridge = AttestBridge()

    with pytest.raises(ValueError, match="COMMIT deontic scope must match action_scope"):
        bridge.wrap_runtime_commit(
            runtime_actor="trusted-runtime:orchestrator",
            content={"execute": True},
            parents=["msg-parent"],
            action_scope="shell_exec",
            deontic=_valid_commit_deontic(scope="state_change"),
        )


def test_commit_rejected_for_parent_binding_mismatch():
    bridge = AttestBridge()

    with pytest.raises(ValueError, match="COMMIT deontic binds.parents must match message parents"):
        bridge.wrap_runtime_commit(
            runtime_actor="trusted-runtime:orchestrator",
            content={"execute": True},
            parents=["msg-parent"],
            action_scope="state_change",
            deontic=_valid_commit_deontic(
                binds={"message": "msg-core-001", "parents": ["msg-other-parent"]}
            ),
        )


def test_commit_rejected_for_external_authority_reference():
    bridge = AttestBridge()

    with pytest.raises(ValueError, match="COMMIT deontic authority\[\] may not use external src: references"):
        bridge.wrap_runtime_commit(
            runtime_actor="trusted-runtime:orchestrator",
            content={"execute": True},
            parents=["msg-parent"],
            action_scope="state_change",
            deontic=_valid_commit_deontic(authority=["src:ticket:1234"]),
        )


def test_commit_accepts_conservative_valid_deontic_payload():
    bridge = AttestBridge()
    msg = bridge.wrap_runtime_commit(
        runtime_actor="trusted-runtime:orchestrator",
        content={"execute": True},
        parents=["msg-parent"],
        action_scope="state_change",
        deontic=_valid_commit_deontic(),
    )

    assert msg["frame"] == "COMMIT"
    assert msg["action_scope"] == "state_change"
    assert msg["deontic"]["type"] == "HUMAN_APPROVAL"


def test_verification_stub_is_unverifiable_not_pass():
    bridge = AttestBridge()
    result = bridge.verify_for_runtime({"frame": "ASSERT", "content": {"x": 1}}, [])

    assert result.decision_effect == "UNVERIFIABLE"
    assert result.soft_flag == ["ATTEST_BRIDGE_DESIGN_STUB_ONLY"]
    assert result.hard_fail == []
    assert result.grounds_resolver_name == "stub-none"
    assert result.authority_resolver_name == "stub-none"


def test_real_attest_bridge_availability_matches_import_gate():
    bridge = AttestBridge(attest_root=None)
    assert bridge.real_available is False
    assert isinstance(attest_agent_conlang_available(), bool)


def test_bridge_plumbing_maps_verifier_output_using_shadow_mock(tmp_path):
    """Unit test of bridge plumbing against a hand-written SHADOW MOCK of
    attest_ref_impl. This proves the bridge maps verifier output into
    AttestVerificationState correctly. It proves NOTHING about the real
    Attest implementation; that is the integration test's job below."""
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
    def __init__(self, known_refs=None, status_overrides=None):
        self.known_refs = known_refs or set()
        self.status_overrides = status_overrides or {}
class AuthorityResolution:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class StaticAuthorityResolver:
    def __init__(self, known_refs=None, status_overrides=None, grants=None):
        self.known_refs = known_refs or set()
        self.status_overrides = status_overrides or {}
        self.grants = grants or {}
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
        resolver_inputs=AttestResolverInputs(runtime_message_refs=["msg:root"]),
        evaluated_at=FIXED_TS,
    )

    assert bridge.real_available is True
    assert result.decision_effect == "PASS"
    assert result.message_id == "shadow-msg-id"
    assert result.profile_id == "shadow-profile"
    assert result.soft_flag == []
    assert result.grounds_resolver_name == "StaticGroundsResolver"
    assert result.authority_resolver_name == "StaticAuthorityResolver"
    assert result.signature_verifier_name == "AcceptAllSignatureVerifier"


def test_bridge_plumbing_supports_configured_deterministic_test_verifier(tmp_path):
    repo_root = tmp_path
    shadow = repo_root / "attest_ref_impl.py"
    shadow.write_text(
        """
from pydantic import BaseModel
class DeploymentProfile(BaseModel):
    name: str = 'shadow-profile'
    signer_public_keys: dict = {}
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
    def __init__(self, known_refs=None, status_overrides=None):
        pass
class AuthorityResolution:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class StaticAuthorityResolver:
    def __init__(self, known_refs=None, status_overrides=None, grants=None):
        pass
class AcceptAllSignatureVerifier:
    pass
class DeterministicSignatureVerifier:
    pass
class AttestVerifier:
    def __init__(self, profile=None, grounds_resolver=None, authority_resolver=None, signature_verifier=None):
        self.profile = profile
        self.signature_verifier = signature_verifier
    def verify(self, msg, adopted_chain=None, known_messages=None):
        return {'hard_fail': [], 'soft_flag': [], 'pass_scope_limit': []}
def load_profile(path=None):
    return DeploymentProfile()
""",
        encoding="utf-8",
    )
    bridge = AttestBridge(
        config=AttestBridgeConfig(signature_verifier_mode="deterministic-test"),
        attest_root=repo_root,
    )
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

    assert result.decision_effect == "PASS"
    assert result.signature_verifier_name == "DeterministicSignatureVerifier"


def test_stub_verification_records_selected_verifier_mode():
    bridge = AttestBridge(config=AttestBridgeConfig(signature_verifier_mode="ed25519-profile"))
    result = bridge.verify_for_runtime({"frame": "ASSERT", "content": {"x": 1}}, [])

    assert result.decision_effect == "UNVERIFIABLE"
    assert result.signature_verifier_name == "stub-none:ed25519-profile"


def test_bridge_falls_back_truthfully_when_loaded_module_throws_shadow_mock(tmp_path):
    """Unit test against a SHADOW MOCK whose profile loader raises: the
    bridge must degrade to the stub with a named real-path-failed flag."""
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
class AuthorityResolution:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


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
    verification = _verification().model_copy(update={
        "grounds_resolver_name": "StaticGroundsResolver",
        "grounds_resolver_config_hash": "grounds-hash-001",
        "authority_resolver_name": "StaticAuthorityResolver",
        "authority_resolver_config_hash": "authority-hash-001",
        "signature_verifier_name": "AcceptAllSignatureVerifier",
        "signature_verifier_config_hash": "sig-hash-001",
    })
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
    assert fragment["attest_grounds_resolver_name"] == "StaticGroundsResolver"
    assert fragment["attest_authority_resolver_config_hash"] == "authority-hash-001"
    assert fragment["attest_signature_verifier_name"] == "AcceptAllSignatureVerifier"
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


# ---------------------------------------------------------------------------
# Real integration seam: runs against the actual AttestAgentConlang sibling
# repo when present (resolved via config paths / ATTEST_AGENT_CONLANG_SRC),
# and SKIPS with a named reason when absent. A skip is an honest receipt;
# a green result produced by a self-authored shadow is not, and one such
# green result previously certified a broken seam (missing sys.modules
# registration in the isolated loader).
# ---------------------------------------------------------------------------

from trusted_runtime.config import load_integration_paths


def _real_attest_root():
    return load_integration_paths().attest_agent_conlang_src


def test_integration_real_attest_verifier_executes_real_semantics():
    root = _real_attest_root()
    if root is None:
        pytest.skip("AttestAgentConlang sibling repo absent; set ATTEST_AGENT_CONLANG_SRC to run the real seam")

    bridge = AttestBridge(attest_root=root)
    assert bridge.real_available is True

    msg = bridge.wrap_adapter_assert(
        layer_name="council",
        content={"finding": "integration probe"},
        grounds=["msg:nonexistent-ground"],
        parents=["msg:root"],
        confidence_interval=(0.7, 0.9),
    )
    result = bridge.verify_for_runtime(
        msg,
        [],
        resolver_inputs=AttestResolverInputs(runtime_message_refs=["msg:root"]),
        evaluated_at=FIXED_TS,
    )

    # The real path must have executed: no stub flag, real verifier identity.
    assert "ATTEST_BRIDGE_DESIGN_STUB_ONLY" not in result.soft_flag
    assert not any(f.startswith("ATTEST_REAL_PATH_FAILED:") for f in result.soft_flag)
    assert result.verifier_version == "attest_ref_impl"
    assert result.decision_effect != "UNVERIFIABLE"

    # And it must exhibit REAL semantics the shadow mock cannot: an
    # unresolvable ground against the empty resolver is a hard failure.
    assert any("GROUNDS_UNRESOLVED" in f or "GROUND" in f for f in result.hard_fail + result.soft_flag)
    assert result.decision_effect == "BLOCK"


def test_integration_real_attest_message_id_is_real_digest():
    root = _real_attest_root()
    if root is None:
        pytest.skip("AttestAgentConlang sibling repo absent; set ATTEST_AGENT_CONLANG_SRC to run the real seam")

    bridge = AttestBridge(attest_root=root)
    msg = bridge.wrap_ingress_request(_action())
    result = bridge.verify_for_runtime(
        msg,
        [],
        resolver_inputs=AttestResolverInputs(runtime_message_refs=[]),
        evaluated_at=FIXED_TS,
    )

    assert "ATTEST_BRIDGE_DESIGN_STUB_ONLY" not in result.soft_flag
    # Real compute_id() is a sha256 hex digest of canonical bytes, and it is
    # NOT the bridge-side stable-json hash (different canonicalization), so
    # equality here would indicate the stub path ran.
    assert len(result.message_id) == 64 and all(c in "0123456789abcdef" for c in result.message_id)
    assert result.message_id != result.canonical_hash
