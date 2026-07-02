from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest
from nacl.signing import SigningKey

from trusted_runtime.config import load_integration_paths
from trusted_runtime.integration.attest_bridge import AttestBridge, AttestBridgeConfig


FIXED_ORDERING_ANCHOR = ["2026-07-02T13:40:00Z", 1]
TEST_SIGNER = "trusted-runtime:test-signer"
TEST_PRIVATE_KEY_B64 = "NSF1zsjFTnC77FmhgKQXkbkq6ACBjl4G7r780Aql5/8"
TEST_PUBLIC_KEY_B64 = "CtxmMupYp26iI84E2O487g4oisNhFWOMcCWsO16IXA0"


def _real_attest_root() -> Path | None:
    return load_integration_paths().attest_agent_conlang_src


def test_real_attest_ed25519_profile_executes_real_signature_verifier_with_local_fixture(tmp_path: Path):
    root = _real_attest_root()
    if root is None:
        pytest.skip("AttestAgentConlang sibling repo absent; set ATTEST_AGENT_CONLANG_SRC to run the real seam")

    profile_path = tmp_path / "attest-profile-ed25519-test.json"
    profile_payload = {
        "profile_id": "attest-ed25519-test",
        "profile_version": "0.2.0-test",
        "warrant_strength_order": {
            "OBSERVED": 5,
            "DERIVED": 4,
            "RETRIEVED": 3,
            "REPORTED": 2,
            "ASSUMED": 1,
        },
        "signature_required_frames": ["ASSERT", "ENDORSE", "DISSENT"],
        "signature_required_retract_when_warranted": True,
        "signature_recommended_frames": ["COMMIT"],
        "state_changing_frames": ["COMMIT"],
        "authority_required_frames": ["COMMIT", "DELEGATE"],
        "grounds_namespaces": {
            "msg": "message identifiers",
            "tool": "tool or execution receipts",
            "src": "external source citations",
            "doc": "document anchors",
            "receipt": "authority or execution receipts",
            "policy": "local policy artifacts",
            "h": "legacy content-addressed message identifiers",
        },
        "grounds_resolution_policy": {
            "unresolved_observed": "hard_fail",
            "unresolved_derived": "hard_fail",
            "unresolved_retrieved": "hard_fail",
            "unresolved_reported": "hard_fail",
            "confidence_without_method_artifact": "soft_flag",
        },
        "external_authority_prefixes": ["src:sentry-event", "src:external-issue", "src:ticket", "src:web", "src:github-issue"],
        "relay_parent_prefixes": ["h:upstream-relay", "relay:hop:"],
        "ordering_anchor_semantics": "timestamp-sequence-total-order",
        "independence_policy_name": "declared-lineage-default",
        "signer_public_keys": {TEST_SIGNER: TEST_PUBLIC_KEY_B64},
        "accepted_authority_types": ["HUMAN_APPROVAL", "POLICY", "CAPABILITY", "DELEGATED", "SANDBOX"],
        "authority_namespaces": ["approval", "policy", "grant", "capability", "sandbox", "receipt"],
        "nonce_required_for_authority": False,
    }
    profile_path.write_text(json.dumps(profile_payload, indent=2), encoding="utf-8")

    bridge = AttestBridge(
        config=AttestBridgeConfig(signature_verifier_mode="ed25519-profile", profile_path=profile_path),
        attest_root=root,
    )
    assert bridge.real_available is True
    assert bridge._real_attest is not None

    message = {
        "frame": "ASSERT",
        "mode": "legible",
        "from": TEST_SIGNER,
        "to": "trusted-runtime:orchestrator",
        "parents": [],
        "ordering_anchor": FIXED_ORDERING_ANCHOR,
        "warrant": {"type": "OBSERVED", "grounds": ["src:web:ed25519-test-fixture"]},
        "content": {"finding": "signed integration test"},
    }
    attest_message = bridge._real_attest["AttestMessage"].model_validate(message)
    signing_key = SigningKey(base64.b64decode(TEST_PRIVATE_KEY_B64 + "===", validate=False))
    signature = signing_key.sign(attest_message.canonical_bytes()).signature
    message["sig"] = "ed25519:" + base64.b64encode(signature).decode("ascii").rstrip("=")

    result = bridge.verify_for_runtime(message, [])

    assert result.signature_verifier_name == "Ed25519SignatureVerifier"
    assert result.decision_effect == "BLOCK"
    assert "ATTEST_BRIDGE_DESIGN_STUB_ONLY" not in result.soft_flag
    assert not any(flag.startswith("ATTEST_REAL_PATH_FAILED:") for flag in result.soft_flag)
    assert "OBSERVED_GROUNDS_NOT_ARTIFACT_BACKED" in result.hard_fail
