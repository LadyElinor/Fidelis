# Authority Grant Store — Design

Status: current patch implements the Phase A store split and replay rejecter,
with some interfaces prepared for Phase B. Approved as the implementation
direction with recorded decisions, deferrals, and invariants; design written
against TrustedRuntime `8c7e66f` and AttestAgentConlang `23f3fc0`.
Implementation in this patch: `authority_store.py` (store, journal, digest,
replay), engine/bridge rewiring with
`PROPOSER_AUTHORITY_INJECTION_ATTEMPTED` flags, the
`verify-authority-digest` CLI rejecter, and constructor-injected authority
resolution. Attest v0.3 consumption (strength/expiry/evaluation-time
enforcement — gap ledger G-1/G-2/G-4 resolved) is a dependent Phase B step
unless reviewed and landed together. Deferred items from the approval remain
deferred: formation-hazard escalation, shared store, enabled
external_attested, overlapping grants, signed journal/boot policy.

## 1. Purpose and the property it must make structural

The taint mechanism (commit `8c7e66f`) marks proposer-supplied authority
evidence as self-certification and denies it a clean PASS. That is honest
instrumentation: the dangerous flow is visible but still exists. This design
removes the flow. After it lands, there is no code path by which content
authored by the proposer of an action can cause any authority reference to
resolve, confer any grant, or override any resolution status. The property is
structural — enforced by what the resolver reads — not behavioral, enforced
by a flag someone must notice.

The one capability proposer context retains is *suggestion*: naming refs the
runtime should attempt to resolve. Suggestion can expand what gets examined.
It can never expand what counts as resolved.

## 2. Trust model

### 2.1 Ownership

The store is orchestrator-held state. It is constructed by the runtime at
startup, mutated only through its explicit API, and handed to the Attest
bridge as the authority resolver. `action.context` never touches it. The
engine keys that today carry grants and overrides (`attest_authority_grants`,
`attest_authority_status_overrides`, `attest_grounds_status_overrides`) are
retired as inputs: if present they are **not consumed**, and their presence
is surfaced as a soft flag `PROPOSER_AUTHORITY_INJECTION_ATTEMPTED:<key>` so
the attempt itself becomes part of the decision record. This is deliberately
louder than silently ignoring: an actor probing the retired channel is
signal.

### 2.2 Insertion channels (provenance of insertion)

Grants enter through a closed set of channels, recorded on the grant:

- `operator` — explicit human action through a runtime-owned surface (CLI,
  review UI). Must carry the operator principal id.
- `policy_boot` — loaded at startup from a policy file the runtime owns.
  Must carry the policy file's content hash, so a receipt can establish
  *which* policy version conferred the grant.
- `delegation` — derived from an existing unexpired, unrevoked grant whose
  type and lattice position permit delegation. Must carry the parent
  `grant_id`. The store enforces at insertion what Attest re-verifies at
  message time: scope ⊆ parent scope, strength ≤ parent strength, expiry ≤
  parent expiry, no cycles.
- `external_attested` — reserved, disabled by default: a future channel for
  grants asserted by an external system with its own signature. Declared now
  so its absence is a stated decision rather than an oversight.

Channel is an enum on the record; an insertion without a valid channel and
the channel's required evidence is rejected. There is deliberately no
`proposer` channel and no code path to add one without touching this file
and its tests.

### 2.3 The suggested / resolved boundary

`AttestResolverInputs` splits into two surfaces with different powers:

- **Runtime-held** (trusted): the store handle for authority; the runtime
  message ledger for grounds. These alone determine resolution outcomes.
- **Proposer-suggested** (untrusted): `suggested_authority_refs` and
  `suggested_message_refs`, from context. These are unioned into the *check
  set* — refs the resolvers will be asked about — and nothing else. A
  suggested ref resolves iff the runtime-held state already resolves it. A
  suggested ref that fails to resolve fails exactly as if the verifier had
  discovered it itself.

Because suggestion cannot change any outcome, it does not taint. The
`RESOLVER_INPUTS_PROPOSER_SUPPLIED` flags retire with the flow they marked;
the injection-attempt flag above replaces them for the rejected keys.
Grounds get the same discipline as authority: the static
known-refs-means-resolved set is replaced by the runtime message ledger
(messages the runtime itself constructed or verified), with evidence-record
sources feeding that ledger as today.

## 3. Grant record

Immutable, content-addressed. Canonical-JSON of the insertion fields, SHA-256
→ `grant_id`. "Update" does not exist: supersession = revoke + insert, and
both artifacts persist.

```
GrantRecord
  grant_id            sha256 hex of canonical insertion fields (derived)
  ref                 authority ref, namespace-checked against the profile's
                      admissible-authority set (§8A.3): approval:, policy:,
                      grant:, capability:, sandbox:
  granted_type        Attest AuthorityType (closed set, §8A.2); NONE rejected
  scope               ActionScope from the declared ontology (§8A.6)
  strength_ceiling    optional; clamps below the type's default lattice
                      position (e.g. a one-shot HUMAN_APPROVAL marked weaker).
                      Never raises. Absent ⇒ type's lattice position.
  expires             optional ISO-8601 UTC instant
  delegates_from      optional parent grant_id (required iff channel=delegation
                      or granted_type=DELEGATED; forbidden otherwise)
  inserted_at         ISO-8601 UTC
  inserted_by         principal id
  channel             operator | policy_boot | delegation | external_attested
  insertion_evidence  channel-specific: approval receipt ref / policy file
                      hash / parent grant_id / external signature ref
Tombstone (separate record, references grant_id)
  revoked_at, revoked_by, reason
```

Identity note: `ref` is the name Attest messages cite; `grant_id` is the
specific conferral. Multiple grant records may exist for one ref over time
(re-approval after expiry); at most one may be active per ref at any instant
— insertion while an active record exists for the ref is rejected until that
record is revoked or expired. This keeps `resolve(ref, at)` deterministic
without a precedence rule.

## 4. Journal and state digest — the first hash consumer

Persistence is an append-only JSONL journal of insertion and revocation
events, each entry carrying `prev_entry_hash` (hash-linked, same receipts-
spine pattern as elsewhere in the constellation). Store state at any instant
is a pure fold over the journal.

`state_digest(at)` = SHA-256 over the sorted `grant_id`s active at `at`. The
bridge records it in the **existing** `authority_resolver_config_hash` field
— no new receipt surface. This is the point where the provenance hashes stop
being merely minted and start being spent: a replay tool reconstructs the
fold at the receipt's `evaluated_at` and **rejects the receipt** if the
digest disagrees. That rejection path is the deliverable that makes the hash
meaningful, and it ships in the same phase as the store (§8, Phase C is not
optional follow-on; see §9).

## 5. Resolution semantics

The store implements Attest's `AuthorityResolver` protocol, evaluation-time
aware:

```
resolve(ref, at) →
  no record for ref                    → unresolved
  active record, unexpired at `at`     → resolved + granted_type,
                                         granted_scope, strength (lattice
                                         position clamped by ceiling),
                                         expires, delegates_from
  record revoked at or before `at`     → revoked
  record expired at or before `at`     → expired
```

`revoked` and `expired` are distinct statuses, not collapsed into
`unresolved`: an authority that existed and was withdrawn is a materially
different audit fact from one never conferred, and Attest's profile-gated
expiry semantics (gap G-3) need the distinction to classify hard vs soft.

`at` defaults to now but is injectable end-to-end — the same instant flows
into `verify(at=...)` and into the receipt, which is what makes replay
possible at all (G-4).

## 6. Attest v0.3 co-design (closes G-1, G-2, G-4)

The store schema and the resolver fields are one design; these land together:

- `AuthorityResolution` gains `expires: Optional[str]` and
  `strength: Optional[str]` (the lattice position the resolver already
  computed — verifier compares, never re-derives store internals).
- `DeploymentProfile` gains the declared authority-strength lattice with the
  §8A.2 default ordering; conformance depends on publishing it, per spec.
- `_walk_delegation` enforces at each hop, at evaluation time: hop unexpired
  (else `AUTHORITY_GRANT_EXPIRED:<ref>`, closing G-2) and effective strength
  = lattice-min over the chain, which must cover what the warrant claims
  (else `DELEGATION_STRENGTH_EXCEEDED`, closing G-1).
- `AttestVerifier.verify(..., at: Optional[datetime])` — injectable
  evaluation time recorded in the verdict, closing G-4. Wall-clock remains
  the default; determinism becomes available rather than mandatory.

Gap ledger updates on landing: G-1, G-2, G-4 → RESOLVED; G-3 becomes
implementable (the profile flag for a trusted ordering authority now has a
store to consult) but is not claimed by this design.

## 7. Threat walkthrough

| Attack | Outcome under this design |
| --- | --- |
| Proposer ships grants/overrides in context | Not consumed; `PROPOSER_AUTHORITY_INJECTION_ATTEMPTED` flag on the decision record |
| Proposer suggests its own approval ref | Checked against store; unresolved unless a trusted channel inserted it |
| Compromised agent self-delegates | `delegation` channel requires parent grant + ceiling checks at insertion; Attest re-verifies the chain at message time — two independent enforcement points |
| Replay of an expired approval | `resolve(ref, at)` → expired; hop-level check catches expired intermediates |
| Post-hoc grant insertion to justify a past act | Receipt's `authority_resolver_config_hash` binds to the digest at `evaluated_at`; replay fold exposes the mismatch |
| Journal tampering | Hash-linked entries; fold verification fails |
| Quiet weakening via "update" | No update primitive exists; supersession leaves both artifacts and a tombstone |

Honest residual: the store trusts its insertion principals. A compromised
operator credential or tampered boot policy file inserts valid grants. The
design makes such insertions *attributable* (channel + evidence + journal),
not impossible — signing the journal and boot policy is future work and is
listed as such, not silently assumed away.

## 8. Integration changes in TrustedRuntime

- New `authority_store.py` (store, journal, digest, resolver adapter) —
  deliberately small and heavily tested; it is the trust root.
- Engine: `_attest_resolver_inputs_for_action` shrinks to suggestion
  extraction + injection-attempt flagging; the bridge receives the store
  resolver and message ledger from the orchestrator, not from inputs.
- Bridge: `verify_for_runtime` takes the resolvers as constructor-injected
  runtime state; `AttestResolverInputs` becomes the suggestion surface only.
- Taint tests evolve rather than vanish: same adversarial fixtures, new
  expected outcomes (not-consumed + flagged, instead of consumed + tainted).
  The adversarial corpus keeps the memory of the old failure mode.

## 9. Phasing

- **Phase A** — store + journal + digest + resolver adapter + engine/bridge
  rewiring + injection-attempt flags. Proposer authority flow ends here.
- **Phase B** — Attest v0.3 fields and enforcement (§6), landing against the
  store as its first real consumer. Gap ledger updated.
- **Phase C** — replay verifier: receipt in, journal fold, accept/reject.
  Ships with A+B, not after; a digest without its rejecter is minted-but-
  unspent legibility, the precursor of theater.

A and B touch different repos and can be built in parallel, but B's tests
should run against A's store rather than synthetic grants, so A merges first.

## 10. Open questions for review

1. **Persistence format**: JSONL journal proposed for continuity with the
   receipts spine. Acceptable for single-process runtime now? (Interface
   isolates this; the question is only about the first backing.)
2. **Store scope**: per-runtime-instance, or shared across the constellation
   (e.g., SOPHRON consulting the same store)? Design assumes per-runtime;
   sharing raises signing questions best deferred to the journal-signing work.
3. **`external_attested` channel**: keep as declared-but-disabled, or omit
   entirely until a concrete external attester exists? Declared-but-disabled
   documents the boundary; omission is smaller surface.
4. **Injection-attempt severity**: soft flag proposed. Escalate to a formation
   hazard so it participates in council review, or is decision-record
   visibility sufficient at this phase?
5. **One-active-grant-per-ref**: the simplest determinism rule. Any real
   workflow needing overlapping grants for one ref (e.g., rotating approvals)?
   If so, precedence semantics must be designed now, not patched in later.
