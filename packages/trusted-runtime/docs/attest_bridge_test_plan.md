# Attest bridge first-pass test plan

This test plan defines the initial implementation checks for wiring Attest into TrustedRuntime as a typed inter-layer message contract.

The target architecture remains:
- **TrustedRuntime** = orchestration/runtime layer
- **Attest** = typed message envelope and verifier
- **CER / SOPHRON** = durable receipt and evidence spine

The goal is not to migrate Attest semantics into TrustedRuntime. The goal is to enforce a clean integration seam.

---

## 1. Placement and seam tests

### T1.1 Bridge module lives at the integration seam
- **Intent:** keep Attest wiring in `src/trusted_runtime/integration/`, not in `shared/` and not mixed into adapter-internal logic.
- **Expected:** bridge imports shared models/enums, but does not redefine the full Attest verifier internally.

### T1.2 Shared models stay runtime-native
- **Intent:** preserve TrustedRuntime ownership of runtime-facing contracts.
- **Expected:** existing `ExecutionDecision`, `CouncilAssessment`, `WarrantAssay`, and `CERRecordBundle` remain valid even when Attest is absent.

### T1.3 Missing Attest dependency degrades truthfully
- **Intent:** avoid fake-success integration.
- **Expected:** missing Attest verifier produces an explicit non-real / unverified state, not a silent pass.

---

## 2. Frame emission invariants

### T2.1 Ingress action wraps as REQUEST or QUERY, not ASSERT
- **Intent:** prevent user/task ingress from masquerading as validated judgment.
- **Expected:** `ProposedAction` ingress emits `REQUEST` by default.

### T2.2 Normal layer outputs emit ASSERT by default
- **Intent:** keep evaluator outputs descriptive rather than prematurely adopting or authorizing.
- **Expected:** council/warrant/telemetry-derived packets default to `ASSERT` unless a stronger frame is intentionally chosen.

### T2.3 Dissent path emits DISSENT, not negative ASSERT disguised as consensus
- **Intent:** preserve structured disagreement.
- **Expected:** explicit dissent helper emits `DISSENT` with traceable parents/grounds.

### T2.4 ENDORSE requires explicit adoption metadata
- **Intent:** enforce the invariant that `ENDORSE` means adoption, not agreement.
- **Expected:** emission fails unless both `adopts` and `adoption_reason` are non-empty.

### T2.5 COMMIT is runtime-owned
- **Intent:** prevent ordinary adapters from authorizing execution.
- **Expected:** only whitelisted runtime actors can emit `COMMIT`.

### T2.6 Non-whitelisted COMMIT emission is rejected
- **Intent:** make the boundary executable, not aspirational.
- **Expected:** adapter-originated `COMMIT` attempt raises a policy error.

---

## 3. Verification-state persistence tests

### T3.1 Verification result persists profile identity
- **Intent:** store verifier truth relative to a concrete deployment profile.
- **Expected:** persisted state includes `profile_id`, `profile_version`, `profile_hash`, and `verifier_version`.

### T3.2 Verification result persists known-message-set hash
- **Intent:** make pass/fail state reproducible relative to corpus context.
- **Expected:** review packet and CER fragment include `known_message_set_hash`.

### T3.3 Hard fail maps to BLOCK
- **Intent:** enforce a clean runtime interpretation surface.
- **Expected:** any non-empty `hard_fail` yields decision effect `BLOCK`.

### T3.4 Soft flag maps to REVIEW when hard fail is absent
- **Intent:** preserve honest uncertainty.
- **Expected:** soft-flagged message yields `REVIEW`, not `PASS`.

### T3.5 Missing verifier maps to UNVERIFIABLE
- **Intent:** preserve truthful degraded mode.
- **Expected:** stub/no-verifier path yields `UNVERIFIABLE`.

---

## 4. Independence and correlation tests

### T4.1 Shared grounds reduce independence
- **Intent:** stop duplicated evidence chains from counting as corroboration.
- **Expected:** overlapping `grounds` produce a correlated or same-origin result.

### T4.2 Shared parents reduce independence
- **Intent:** account for derivation from the same upstream message set.
- **Expected:** overlapping parents prevent full-independence classification.

### T4.3 Same signer collapses to same-origin
- **Intent:** separate multiple statements from one actor from independent corroboration.
- **Expected:** matching signer lineage yields `same-origin` and low score.

### T4.4 Same operator collapses to same-origin even with different adapters
- **Intent:** avoid false plurality inside one operator boundary.
- **Expected:** operator overlap is enough to block independent-corroboration credit.

### T4.5 Same adapter family downgrades independence
- **Intent:** recognize correlated pipelines.
- **Expected:** same-family outputs produce at least `correlated`, not `independent`, unless overridden by stronger evidence policy.

### T4.6 No overlap across relevant dimensions can classify as independent
- **Intent:** allow genuine corroboration when structure supports it.
- **Expected:** no shared signer/operator/grounds/parents can yield `independent`.

---

## 5. Dissent preservation tests

### T5.1 Live dissent IDs survive into final review packet
- **Intent:** preserve non-consensus state.
- **Expected:** unresolved dissent IDs appear in the final packet surface.

### T5.2 Retracted dissent is removed only when explicitly superseded or retracted
- **Intent:** prevent silent erasure.
- **Expected:** dissent disappears from unresolved set only when referenced by `RETRACT` or explicit supersession.

### T5.3 Positive endorsement does not erase prior dissent automatically
- **Intent:** keep disagreement history legible.
- **Expected:** ENDORSE alone does not clear unrelated dissent IDs.

---

## 6. CER receipt integration tests

### T6.1 CER fragment stores more than raw Attest message ID
- **Intent:** preserve profile-relative verification context.
- **Expected:** CER fragment includes message ID, canonical hash, profile identity, verifier version, known-message-set hash, and decision effect.

### T6.2 CER fragment can embed runtime independence judgment
- **Intent:** preserve the separation between Attest verification and runtime correlation policy.
- **Expected:** receipt fragment optionally includes `attest_independence` payload.

### T6.3 Identical verification inputs yield deterministic CER fragment
- **Intent:** maintain receipt reproducibility.
- **Expected:** same verification inputs produce byte-stable serialized fragment output.

---

## 7. Runtime policy interaction tests

### T7.1 Verified message can still require REVIEW for independence reasons
- **Intent:** separate verifier success from corroboration sufficiency.
- **Expected:** `PASS` verification plus `same-origin` independence yields runtime review/escalation.

### T7.2 COMMIT packet must inherit runtime disposition constraints
- **Intent:** Attest should not bypass TrustedRuntime gating.
- **Expected:** blocked or confirm-human runtime disposition prevents emission of executable commit path.

### T7.3 Attest success does not upgrade stubbed external layers to real
- **Intent:** preserve adapter provenance truthfulness.
- **Expected:** bridge verification success does not mutate `AdapterProvenance` for council/warrant/tas/cer.

---

## 8. First concrete pytest targets

Suggested initial test module:
- `tests/test_attest_bridge.py`

Suggested first implemented tests:
1. `test_endorse_requires_adopts_and_adoption_reason`
2. `test_commit_rejected_for_non_whitelisted_emitter`
3. `test_verification_stub_is_unverifiable_not_pass`
4. `test_shared_grounds_reduce_independence`
5. `test_same_operator_prevents_independent_corroboration`
6. `test_unresolved_dissent_ids_preserved_without_retract`
7. `test_cer_receipt_fragment_includes_profile_and_known_message_hash`
8. `test_verified_but_same_origin_message_still_requires_review`

---

## 9. Non-goals for first pass

These should **not** be claimed as complete in the first implementation pass:
- full transitive grounds-cycle enforcement beyond current Attest verifier behavior
- complete signer/lineage cryptography
- full multi-profile deployment management
- all-real adapter execution through the entire TrustedRuntime stack
- semantic migration of ethics/warrant/telemetry logic into TrustedRuntime

The first pass is about a clean seam, explicit invariants, and honest persistence of verification state.
