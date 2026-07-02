from __future__ import annotations

import json
from pathlib import Path

import pytest

from trusted_runtime.config import load_integration_paths
from trusted_runtime.integration.attest_bridge import AttestBridge, AttestBridgeConfig


def _real_attest_root() -> Path | None:
    return load_integration_paths().attest_agent_conlang_src


def test_default_attest_profile_does_not_currently_claim_signer_keys_when_empty():
    root = _real_attest_root()
    if root is None:
        pytest.skip("AttestAgentConlang sibling repo absent; set ATTEST_AGENT_CONLANG_SRC to inspect real profile")

    profile_path = root / "attest-profile-default-v02.json"
    assert profile_path.exists()

    payload = json.loads(profile_path.read_text(encoding="utf-8"))
    signer_keys = payload.get("signer_public_keys", {})

    assert isinstance(signer_keys, dict)
    if signer_keys == {}:
        assert signer_keys == {}


def test_ed25519_profile_mode_is_configurable_without_claiming_real_success():
    bridge = AttestBridge(config=AttestBridgeConfig(signature_verifier_mode="ed25519-profile"))
    result = bridge.verify_for_runtime({"frame": "ASSERT", "content": {"x": 1}}, [])

    assert result.decision_effect == "UNVERIFIABLE"
    assert result.signature_verifier_name == "stub-none:ed25519-profile"
