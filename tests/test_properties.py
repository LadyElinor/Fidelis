import base64

from nacl.signing import SigningKey
from attest_ref_impl import (
    AttestMessage,
    AttestVerifier,
    Ed25519SignatureVerifier,
    StaticAuthorityResolver,
    StaticGroundsResolver,
    load_profile,
)
from hypothesis import given, strategies as st


NONCRYPTO_PROFILE = load_profile()
NONCRYPTO_PROFILE.name = "attest-test-noncrypto"
NONCRYPTO_PROFILE.signature_required_frames = set()
NONCRYPTO_PROFILE.signature_required_retract_when_warranted = False
NONCRYPTO_PROFILE.signature_recommended_frames = set()

SIGNING_KEY = SigningKey.generate()
VERIFY_KEY_B64 = base64.b64encode(bytes(SIGNING_KEY.verify_key)).decode("ascii")


def sign_ed25519(msg: AttestMessage) -> str:
    signature = SIGNING_KEY.sign(msg.canonical_bytes()).signature
    return "ed25519:" + base64.b64encode(signature).decode("ascii")


@given(st.text(min_size=1, max_size=40).map(lambda s: "tool:" + s))
def test_prefixed_fabricated_observed_fails_closed(ref: str):
    verifier = AttestVerifier(
        profile=NONCRYPTO_PROFILE,
        grounds_resolver=StaticGroundsResolver(set()),
        authority_resolver=StaticAuthorityResolver(set()),
    )
    msg = AttestMessage.model_validate(
        {
            "frame": "ASSERT",
            "mode": "legible",
            "from": "agent:tester",
            "to": "agent:planner",
            "parents": [],
            "ordering_anchor": ["2026-06-29T20:00:00Z", 1],
            "warrant": {"type": "OBSERVED", "confidence": [0.9, 0.99], "grounds": [ref]},
            "content": "fabricated observed claim",
        }
    )
    result = verifier.verify(msg)
    assert "OBSERVED_GROUNDS_NOT_ARTIFACT_BACKED" in result["hard_fail"]


@given(st.text(min_size=1, max_size=20), st.text(min_size=1, max_size=20))
def test_nfc_nfd_normalize_to_same_id(prefix: str, stem: str):
    a = AttestMessage.model_validate(
        {
            "frame": "ASSERT",
            "mode": "legible",
            "from": "agent:tester",
            "to": "agent:planner",
            "parents": [],
            "ordering_anchor": ["2026-06-29T20:00:00Z", 2],
            "warrant": {"type": "ASSUMED", "grounds": []},
            "content": prefix + "é" + stem,
        }
    )
    b = AttestMessage.model_validate(
        {
            "frame": "ASSERT",
            "mode": "legible",
            "from": "agent:tester",
            "to": "agent:planner",
            "parents": [],
            "ordering_anchor": ["2026-06-29T20:00:00Z", 2],
            "warrant": {"type": "ASSUMED", "grounds": []},
            "content": prefix + "e\u0301" + stem,
        }
    )
    assert a.compute_id() == b.compute_id()


def test_authority_receipt_must_bind_message_and_parents_and_nonce():
    verifier = AttestVerifier(
        profile=load_profile(),
        grounds_resolver=StaticGroundsResolver({"src:sentry-event:resolution-text"}),
        authority_resolver=StaticAuthorityResolver({"approval:ops-001"}),
    )
    msg = AttestMessage.model_validate(
        {
            "frame": "COMMIT",
            "mode": "legible",
            "from": "agent:operator-1",
            "to": "agent:executor-0",
            "parents": ["relay:hop:1"],
            "ordering_anchor": ["2026-06-30T14:59:00Z", 200],
            "warrant": {"type": "REPORTED", "grounds": ["src:sentry-event:resolution-text"]},
            "authority_receipts": [
                {
                    "kind": "human_approval",
                    "receipt_ref": "approval:ops-001",
                    "scope": "state_change",
                    "issuer": "human:operator",
                    "bound_message_id": "deadbeef",
                    "bound_parent_ids": ["relay:hop:other"],
                    "expires_at": "2099-01-01T00:00:00Z",
                    "nonce": "nonce-123",
                }
            ],
            "content": "Apply remediation from external issue.",
        }
    )
    result = verifier.verify(msg)
    assert "AUTHORITY_RECEIPT_BINDING_INVALID" in result["hard_fail"]


def test_authority_receipt_requires_resolution_and_nonce():
    verifier = AttestVerifier(
        profile=load_profile(),
        grounds_resolver=StaticGroundsResolver({"src:sentry-event:resolution-text"}),
        authority_resolver=StaticAuthorityResolver(set()),
    )
    temp = AttestMessage.model_validate(
        {
            "frame": "COMMIT",
            "mode": "legible",
            "from": "agent:operator-1",
            "to": "agent:executor-0",
            "parents": ["relay:hop:1"],
            "ordering_anchor": ["2026-06-30T14:59:00Z", 200],
            "warrant": {"type": "REPORTED", "grounds": ["src:sentry-event:resolution-text"]},
            "content": "Apply remediation from external issue.",
        }
    )
    msg = AttestMessage.model_validate(
        {
            **temp.model_dump(by_alias=True),
            "authority_receipts": [
                {
                    "kind": "human_approval",
                    "receipt_ref": "approval:never-issued",
                    "scope": "state_change",
                    "issuer": "human:operator",
                    "bound_message_id": temp.compute_core_id(),
                    "bound_parent_ids": temp.parents,
                    "expires_at": "2099-01-01T00:00:00Z",
                    "nonce": None,
                }
            ],
        }
    )
    result = verifier.verify(msg)
    assert any(code.startswith("AUTHORITY_RECEIPT_UNRESOLVED") for code in result["hard_fail"])


def test_real_ed25519_signature_vector_verifies():
    profile = load_profile()
    profile.signer_public_keys = {"agent:crypto-tester": VERIFY_KEY_B64}
    verifier = AttestVerifier(
        profile=profile,
        grounds_resolver=StaticGroundsResolver({"src:doi:10.1234/example/p7"}),
        authority_resolver=StaticAuthorityResolver(set()),
        signature_verifier=Ed25519SignatureVerifier(profile.signer_public_keys),
    )
    msg = AttestMessage.model_validate(
        {
            "frame": "ASSERT",
            "mode": "legible",
            "from": "agent:crypto-tester",
            "to": "agent:planner-0",
            "parents": [],
            "ordering_anchor": ["2026-06-30T15:00:00Z", 1],
            "warrant": {"type": "RETRIEVED", "grounds": ["src:doi:10.1234/example/p7"]},
            "content": "Canonical signing vector.",
        }
    )
    payload = msg.model_dump(by_alias=True)
    payload["sig"] = sign_ed25519(msg)
    signed = AttestMessage.model_validate(payload)
    result = verifier.verify(signed)
    assert result == {"hard_fail": [], "soft_flag": [], "pass_scope_limit": []}
