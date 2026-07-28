# Attest spec/implementation gap ledger

This ledger is the single authoritative record of known divergences between `attest-spec.md` and `attest_ref_impl.py`. Its purpose is to prevent silent deviation: the implementation may be a conservative subset of the spec, or temporarily stricter than the spec, only if the divergence is recorded here. A divergence absent from this ledger is a defect, not a design decision.

Status vocabulary: **OPEN** (divergence exists), **RESOLVED** (spec and impl reconciled; entry retained for history).

---

## G-1. Delegation strength ceiling not enforced — RESOLVED (v0.3)

- **Spec:** §8A.5 requires that the effective *scope and strength* of `DELEGATED` authority not exceed what the delegating principal held.
- **Impl:** `_walk_delegation` enforces the scope ceiling only. `AuthorityResolution` carries no strength field, so a chain can launder a weak root into a strong effective authority without detection.
- **Consequence:** strength-ceiling violations pass verification.
- **Resolution:** `AuthorityResolution.strength` reports the resolver's lattice position; `DeploymentProfile.authority_strength_lattice` publishes the §8A.2 default ordering; `_walk_delegation` enforces the ceiling hop-to-hop (each hop's strength must not exceed its parent's — the walk seeds with no claim, since effective strength is the chain minimum) and emits `DELEGATION_STRENGTH_EXCEEDED:<ref>`. First real consumer: the TrustedRuntime AuthorityGrantStore, which also enforces the ceiling independently at insertion time.

## G-2. Grant-level expiry not checked along delegation chains — RESOLVED (v0.3)

- **Spec:** §8A.7.6 requires expiry to be enforced where present. An expired delegating grant cannot confer live authority.
- **Impl:** only the top-level warrant's `expires` is checked. `AuthorityResolution` has no expiry field, so an expired intermediate grant passes.
- **Resolution:** `AuthorityResolution.expires` added; every hop of `_walk_delegation` and every directly-resolved authority is checked against the evaluation instant, emitting `AUTHORITY_GRANT_EXPIRED:<ref>`.

## G-3. Replay depends on injected state, not verifier-local proof — OPEN, narrowed in v0.3

- **Spec:** §8A.7.6 makes expired or replayed authority *malformed only where a trusted ordering authority exists*; without one, expiry and replay degrade to a soft audit signal (consistent with the retract-ordering limit, §18).
- **Impl (current):** expiry classification now follows a profile flag declaring `trusted_ordering_authority`: expired authority hard-fails only when such an authority is declared, otherwise it emits `AUTHORITY_EXPIRED_SOFT`. In that same mode, `nonce` becomes required for authority-required frames. The verifier now also accepts an injected `NonceReplayChecker`, can emit `AUTHORITY_NONCE_REPLAYED` when the checker reports prior consumption, and ships a minimal in-memory replay checker that consumes a nonce on first use and rejects it on repeat.
- **Remaining gap:** replay detection is no longer absent and is no longer purely delegated, but the built-in checker is only process-local and ephemeral. The reference verifier still has no durable or externally authoritative ordering service of its own, so replay proof across processes or restarts remains delegated.
- **Remediation:** either provide a durable replay cache implementation behind the trusted-ordering-authority flag or bind the verifier to an external ordering/replay authority with explicit availability and failure semantics.
- **Note (v0.3):** this is now a narrower and more explicit gap than before: expiry semantics no longer over-hard-fail in ordering-authority-free profiles, replay detection has a real hook plus a minimal reference implementation, but authoritative replay state is still not built in.

## G-4. Verification is wall-clock-dependent — RESOLVED (v0.3)

- **Spec:** verification verdicts should be reproducible receipts; nothing in the spec licenses an implicit, unrecorded input.
- **Impl:** `_authority_unexpired` calls `datetime.now(timezone.utc)` internally. The same message can verify differently on different days with no record of the evaluation time, so a verdict cannot be deterministically replayed.
- **Resolution:** `verify(..., at=None)` accepts an injectable evaluation instant (wall clock remains the default), plumbs it through deontic expiry and the delegation walk, and records `evaluated_at` in the verdict. Same message + same `at` now yields byte-identical verdicts; TrustedRuntime binds the same instant into its receipts and store digests, making replay end-to-end.

## G-5. Covering-binding clause unimplemented (conservative subset) — OPEN, documented

- **Spec:** §8A.4 permits `binds.message` to be "establishable as covering" the message, e.g. an approval issued against the adopted-chain root the message derives from.
- **Impl:** `_deontic_binds` requires exact core-ID equality and exact `parents` equality. Chain-root covering is rejected.
- **Classification:** acceptable as a conservative subset — everything the impl accepts, the spec accepts; not vice versa. Recorded here so the deviation is explicit rather than silent. Any future covering implementation must define "establishable" mechanically (adopted-chain walk with the same cycle/ancestry checks as §8A.5) before landing.

## G-6. Delegation error reporting is short-circuiting — RESOLVED (v0.3)

- **Was:** `_walk_delegation` aggregated branches with `all(...)`, which short-circuited: after the first failing branch, remaining branches were unexplored. Verdicts could still be correct while multi-branch audit errors were incomplete.
- **Resolution:** delegation branches are now all evaluated before aggregation, so the verifier can report multiple failing branches in a single verdict while preserving the same overall pass/fail behavior.

---

## Resolved in this change set

## G-7. Core-ID / binding circularity — RESOLVED

- **Was:** §8A.4 required `binds.message` to equal "the message's own computed ID" while §10.2/§8A.7.7 made the deontic object identity-bearing — jointly unimplementable. The impl bound to a deontic-excluded core digest the spec never defined.
- **Now:** §10.2.1 normatively defines the core ID, its role split against the full message ID, and the prohibitions in each direction. §8A.4 binds to the core ID and states the non-circularity rationale. Delta §1.4 reconciled to migrated field names.

## G-8. Retired `authority_receipts` silently ignored — RESOLVED

- **Was:** envelope models used pydantic's default `extra="ignore"`; the serialized corpus (Cases 4, 13) still carried `authority_receipts`, and the harness overwrote those cases with programmatically built `deontic` objects — the document displayed one envelope while the harness tested another.
- **Now:** all envelope models (`AttestMessage`, `Warrant`, `DeonticWarrant`, `DeonticBinding`) are `extra="forbid"`; the corpus carries the real `deontic` envelopes with frozen, deterministically computed core-ID bindings; the harness injection code is deleted so the corpus is the tested artifact; four regression tests assert that retired and unknown fields are rejected at parse time, at the envelope, deontic, and binds levels.

## G-9. `general` scope coverage semantics undefined — RESOLVED

- **Was:** the impl treated `general` as covering every `action_scope`; the spec listed `general` in the ontology without defining coverage.
- **Now:** §8A.6 defines `general` as the top element, exact match otherwise, and requires extended ontologies to publish their partial order.

## G-10. README crypto claim drift — RESOLVED

- **Was:** README claimed conformance examples "in deterministic test-vector form, not yet real Ed25519" while the harness generated a fresh Ed25519 key per run — real Ed25519 verification, and not deterministic.
- **Now:** README states the accurate position: runtime-generated Ed25519 signature round-trips exist; fixed cross-implementation interop vectors do not yet.
