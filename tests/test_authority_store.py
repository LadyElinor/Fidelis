from __future__ import annotations

"""Trust-root tests for the authority grant store.

Every invariant from the approved design is asserted here: closed channels
with evidence enforcement, namespace/type discipline, one-active-per-ref,
immutability with tombstone revocation, distinct resolution outcomes,
delegation ceilings (scope, strength, expiry, cycle), journal fold with
hash-chain tamper detection, and digest replay with a real reject path.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from trusted_runtime.authority_store import (
    AuthorityGrantStore,
    GrantStoreError,
    replay_verify_digest,
)

T0 = datetime(2026, 7, 2, 12, 0, 0, tzinfo=timezone.utc)


def _store(tmp_path: Path | None = None) -> AuthorityGrantStore:
    return AuthorityGrantStore(journal_path=(tmp_path / "authority.jsonl") if tmp_path else None)


def _insert_root(store, ref="approval:ops-1", scope="state_change", expires=None, at=T0):
    return store.insert_grant(
        ref=ref, granted_type="HUMAN_APPROVAL", scope=scope, channel="operator",
        inserted_by="user:operator-1", insertion_evidence="receipt:approval-evt-1",
        expires=expires, at=at,
    )


# -- channels and evidence -----------------------------------------------------

def test_proposer_channel_does_not_exist():
    with pytest.raises(GrantStoreError, match="unknown insertion channel"):
        _store().insert_grant(
            ref="approval:x", granted_type="HUMAN_APPROVAL", scope="general",
            channel="proposer", inserted_by="agent", insertion_evidence="claimed",
        )


def test_external_attested_declared_but_disabled():
    with pytest.raises(GrantStoreError, match="declared but disabled"):
        _store().insert_grant(
            ref="approval:x", granted_type="HUMAN_APPROVAL", scope="general",
            channel="external_attested", inserted_by="ext", insertion_evidence="sig:x",
        )


def test_channel_evidence_required():
    with pytest.raises(GrantStoreError, match="insertion_evidence"):
        _store().insert_grant(
            ref="policy:p1", granted_type="POLICY", scope="general",
            channel="policy_boot", inserted_by="runtime:boot", insertion_evidence="  ",
        )
    with pytest.raises(GrantStoreError, match="principal"):
        _store().insert_grant(
            ref="policy:p1", granted_type="POLICY", scope="general",
            channel="policy_boot", inserted_by="", insertion_evidence="sha256:policyfile",
        )


def test_namespace_and_type_discipline():
    with pytest.raises(GrantStoreError, match="admissible authority namespace"):
        _insert_root(_store(), ref="src:external-thing")
    with pytest.raises(GrantStoreError, match="bottom element"):
        _store().insert_grant(
            ref="approval:x", granted_type="NONE", scope="general",
            channel="operator", inserted_by="user:o", insertion_evidence="e",
        )


# -- immutability, supersession, determinism ------------------------------------

def test_one_active_grant_per_ref():
    s = _store()
    _insert_root(s)
    with pytest.raises(GrantStoreError, match="already has an active grant"):
        _insert_root(s)


def test_supersession_is_revoke_plus_insert_and_both_persist():
    s = _store()
    g1 = _insert_root(s)
    s.revoke_grant(g1.grant_id, revoked_by="user:operator-1", reason="rotating approval", at=T0 + timedelta(hours=1))
    g2 = _insert_root(s, at=T0 + timedelta(hours=2))
    assert g1.grant_id != g2.grant_id
    audit = s.audit_records()
    assert len(audit) == 2
    assert audit[0]["revocation"]["reason"] == "rotating approval"
    assert audit[1]["revocation"] is None


def test_double_revocation_rejected():
    s = _store()
    g = _insert_root(s)
    s.revoke_grant(g.grant_id, revoked_by="u", reason="r")
    with pytest.raises(GrantStoreError, match="already revoked"):
        s.revoke_grant(g.grant_id, revoked_by="u", reason="again")


# -- distinct resolution outcomes ------------------------------------------------

def test_resolution_outcomes_are_materially_distinct():
    s = _store()
    assert s.resolve("approval:never", at=T0).status == "unresolved"

    g = _insert_root(s, expires=(T0 + timedelta(days=1)).isoformat(), at=T0)
    assert s.resolve("approval:ops-1", at=T0 + timedelta(hours=1)).status == "resolved"
    assert s.resolve("approval:ops-1", at=T0 + timedelta(days=2)).status == "expired"

    s.revoke_grant(g.grant_id, revoked_by="user:sec", reason="incident", at=T0 + timedelta(hours=2))
    res = s.resolve("approval:ops-1", at=T0 + timedelta(hours=3))
    assert res.status == "revoked"
    assert "incident" in (res.detail or "")
    # Before the revocation instant, it was still resolved.
    assert s.resolve("approval:ops-1", at=T0 + timedelta(hours=1)).status == "resolved"


def test_resolution_is_evaluation_time_aware_before_insertion():
    s = _store()
    _insert_root(s, at=T0)
    assert s.resolve("approval:ops-1", at=T0 - timedelta(hours=1)).status == "unresolved"


# -- delegation ceilings ---------------------------------------------------------

def _delegate(s, parent, ref="grant:agent-1", scope="state_change", expires=None,
              ceiling=None, at=T0 + timedelta(minutes=5)):
    return s.insert_grant(
        ref=ref, granted_type="DELEGATED", scope=scope, channel="delegation",
        inserted_by="runtime:orchestrator", insertion_evidence=parent.grant_id,
        delegates_from=parent.grant_id, expires=expires, strength_ceiling=ceiling, at=at,
    )


def test_delegation_requires_parent_and_matching_evidence():
    s = _store()
    with pytest.raises(GrantStoreError, match="delegates_from"):
        s.insert_grant(ref="grant:a", granted_type="DELEGATED", scope="general",
                       channel="delegation", inserted_by="r", insertion_evidence="x")
    parent = _insert_root(s, scope="general", expires=(T0 + timedelta(days=7)).isoformat())
    with pytest.raises(GrantStoreError, match="evidence must be the parent"):
        s.insert_grant(ref="grant:a", granted_type="DELEGATED", scope="general",
                       channel="delegation", inserted_by="r", insertion_evidence="other",
                       delegates_from=parent.grant_id,
                       expires=(T0 + timedelta(days=1)).isoformat())


def test_delegated_scope_must_not_exceed_parent():
    s = _store()
    parent = _insert_root(s, scope="shell_exec", expires=(T0 + timedelta(days=7)).isoformat())
    with pytest.raises(GrantStoreError, match="exceeds parent scope"):
        _delegate(s, parent, scope="general", expires=(T0 + timedelta(days=1)).isoformat())


def test_delegated_expiry_must_be_set_and_bounded_by_parent():
    s = _store()
    parent = _insert_root(s, scope="general", expires=(T0 + timedelta(days=7)).isoformat())
    with pytest.raises(GrantStoreError, match="must not exceed parent expiry"):
        _delegate(s, parent, expires=None)
    with pytest.raises(GrantStoreError, match="must not exceed parent expiry"):
        _delegate(s, parent, expires=(T0 + timedelta(days=30)).isoformat())
    child = _delegate(s, parent, expires=(T0 + timedelta(days=1)).isoformat())
    assert child.delegates_from == parent.grant_id


def test_delegation_from_revoked_or_expired_parent_rejected():
    s = _store()
    parent = _insert_root(s, scope="general", expires=(T0 + timedelta(days=7)).isoformat())
    s.revoke_grant(parent.grant_id, revoked_by="u", reason="r", at=T0 + timedelta(minutes=1))
    with pytest.raises(GrantStoreError, match="revoked and cannot delegate"):
        _delegate(s, parent, at=T0 + timedelta(minutes=2), expires=(T0 + timedelta(days=1)).isoformat())


def test_delegated_strength_inherits_chain_minimum_via_ceiling():
    s = _store()
    parent = _insert_root(s, scope="general", expires=(T0 + timedelta(days=7)).isoformat())
    weak_parent_res = s.resolve(parent.ref, at=T0 + timedelta(minutes=1))
    assert weak_parent_res.strength == 3
    child = _delegate(s, parent, ceiling=1, expires=(T0 + timedelta(days=1)).isoformat())
    res = s.resolve(child.ref, at=T0 + timedelta(minutes=10))
    assert res.status == "resolved" and res.strength == 1


def test_strength_ceiling_never_raises():
    s = _store()
    with pytest.raises(GrantStoreError, match="ceilings clamp, never raise"):
        _insert_root(_store(), ref="approval:x")
        s.insert_grant(ref="sandbox:box", granted_type="SANDBOX", scope="general",
                       channel="operator", inserted_by="u", insertion_evidence="e",
                       strength_ceiling=3)


# -- journal: fold, tamper detection, replay -------------------------------------

def test_journal_fold_reconstructs_state(tmp_path):
    s = _store(tmp_path)
    g = _insert_root(s, expires=(T0 + timedelta(days=1)).isoformat())
    s.revoke_grant(g.grant_id, revoked_by="u", reason="rotate", at=T0 + timedelta(hours=1))
    _insert_root(s, at=T0 + timedelta(hours=2))

    reloaded = AuthorityGrantStore(journal_path=tmp_path / "authority.jsonl")
    assert reloaded.audit_records() == s.audit_records()
    assert reloaded.state_digest(T0 + timedelta(hours=3)) == s.state_digest(T0 + timedelta(hours=3))


def test_journal_tamper_detected(tmp_path):
    s = _store(tmp_path)
    _insert_root(s)
    journal = tmp_path / "authority.jsonl"
    tampered = journal.read_text().replace("user:operator-1", "user:attacker-9")
    journal.write_text(tampered)
    with pytest.raises(GrantStoreError, match="hash mismatch"):
        AuthorityGrantStore(journal_path=journal)


def test_replay_verifier_accepts_true_digest_and_rejects_false(tmp_path):
    s = _store(tmp_path)
    _insert_root(s)
    at = (T0 + timedelta(minutes=5)).isoformat()
    digest = s.state_digest(T0 + timedelta(minutes=5))

    ok = replay_verify_digest(tmp_path / "authority.jsonl", at, digest)
    assert ok.accept and ok.computed_digest == digest

    bad = replay_verify_digest(tmp_path / "authority.jsonl", at, "0" * 64)
    assert not bad.accept and "mismatch" in bad.reason


def test_replay_verifier_rejects_post_hoc_insertion(tmp_path):
    """A receipt taken before a grant existed must not verify against a
    journal where the grant was inserted later-but-backdated is impossible
    (insertion time is part of the fold); the digest at the receipt's
    evaluated_at simply differs."""
    s = _store(tmp_path)
    receipt_at = T0 + timedelta(minutes=1)
    receipt_digest = s.state_digest(receipt_at)  # empty store at receipt time

    _insert_root(s, at=T0 + timedelta(minutes=30))  # post-hoc grant
    later_digest = s.state_digest(T0 + timedelta(hours=1))
    assert later_digest != receipt_digest

    verdict = replay_verify_digest(tmp_path / "authority.jsonl", receipt_at.isoformat(), receipt_digest)
    assert verdict.accept  # the honest receipt still verifies at its own instant
    forged = replay_verify_digest(tmp_path / "authority.jsonl", receipt_at.isoformat(), later_digest)
    assert not forged.accept  # claiming the later state at the earlier instant is rejected
