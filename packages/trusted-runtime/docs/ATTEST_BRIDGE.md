# Attest bridge seam

This document explains the current TrustedRuntime <-> Attest integration stance.

## Purpose

The Attest bridge is an **L5 integration seam**, not a semantic merger.

Its job is to let TrustedRuntime:
- wrap ingress and selected inter-layer messages in an Attest-shaped envelope,
- preserve profile-relative verification state,
- surface correlation/independence facts honestly,
- and emit CER-ready receipt fragments,

without moving Attest’s verifier semantics into TrustedRuntime and without collapsing EthicsCouncil, meaning-assay, or CER/SOPHRON into one repo.

## Current status

Current first pass is intentionally modest:
- `src/trusted_runtime/integration/attest_bridge.py` exists as a concrete first-pass seam,
- `assemble_execution_decision()` now records an Attest-shaped ingress message,
- the bridge emits explicit process provenance,
- report rendering now surfaces bridge presence and verification status,
- the pytest module `tests/test_attest_bridge.py` covers the first contract invariants,
- and a real `AttestAgentConlang` import/wiring path now exists behind an availability gate.

This is still **not** yet a full all-real end-to-end Attest runtime.
Current behavior is:
- when `AttestAgentConlang` is importable, the bridge can run real structural/profile verifier calls for the bridged message surface,
- when it is unavailable, or when the real path fails, the bridge falls back truthfully to `UNVERIFIABLE` stub mode rather than pretending success,
- and the current real-path verifier wiring should not yet be overread as a strong cryptographic trust claim by itself.

## Invariants

The first-pass seam encodes these invariants:

1. **`ENDORSE` means adoption, not mere agreement**
   - `adopts` and `adoption_reason` are mandatory.

2. **`COMMIT` is runtime-owned**
   - only whitelisted runtime actors may emit `COMMIT`.

3. **`DISSENT` is non-erasing**
   - unresolved dissent must remain visible unless explicitly retracted or superseded.

4. **Independence is runtime-computed**
   - overlap across grounds, parents, signer/operator lineage, and adapter-family signals is evaluated by TrustedRuntime.

5. **CER stores profile-relative verification state**
   - not just raw Attest IDs/hashes, but also profile identity, verifier version, known-message-set hash, and decision effect.

## Verifier modes

The bridge now supports explicit verifier-mode selection via `AttestBridgeConfig.signature_verifier_mode`.

Current supported modes are:

- `accept-all`
  - compatibility/default mode for structural seam wiring
  - useful for proving import/profile/plumbing shape
  - not a cryptographic trust claim
- `deterministic-test`
  - controlled test-only verifier mode when the sibling Attest implementation exposes it
  - useful for repeatable seam tests without pretending real signatures
- `ed25519-profile`
  - profile-driven verifier path using signer keys from the loaded Attest deployment profile
  - should only be treated as meaningful when the active profile actually supplies signer keys and the message surface exercises signatures

A configured mode is part of the runtime truth surface and is reported in bridge verification state.

## Non-claims

This seam should not be overstated.
Current work does **not** claim:
- stronger cryptographic trust than the currently configured verifier path actually provides,
- a successful `ed25519-profile` claim when the active profile has no signer keys configured,
- replay-safe or wall-clock-stable verification semantics beyond current Attest behavior,
- transitive grounds-cycle closure beyond current Attest behavior,
- or a complete reproducible all-real end-to-end release artifact.

## Files

- `src/trusted_runtime/integration/attest_bridge.py`
- `docs/attest_bridge_test_plan.md`
- `tests/test_attest_bridge.py`

## Resolver input trust boundary

Resolver inputs can mark grounds and authority as RESOLVED, confer grants, and
override resolution status. Where those inputs come from is therefore a trust
decision, and the current engine accepts them from two sources with very
different standing:

- **Runtime-observed**: known message refs derived from evidence records the
  runtime itself collected. These are trusted.
- **Proposer-supplied**: `attest_known_message_refs`,
  `attest_known_authority_refs`, `attest_authority_grants`,
  `attest_grounds_status_overrides`, and `attest_authority_status_overrides`
  read from the proposed action's own `context`. These are authored by the
  party whose action is being verified - self-certification, the structure
  the independence invariant exists to forbid.

Current patch semantics (grant-store split, approved design in
AUTHORITY_GRANT_STORE.md): the retired trust-conferring keys are **not
consumed at all**. The authority resolver is the orchestrator-owned
AuthorityGrantStore, constructor-injected into the bridge. Grounds checking
is seeded by runtime-observed refs, and proposer suggestions
(`attest_suggested_message_refs` / `attest_suggested_authority_refs`) expand
what gets checked without expanding what counts as resolved. Presence of any
retired key is surfaced as a
`PROPOSER_AUTHORITY_INJECTION_ATTEMPTED:<key>` soft flag on every
verification path, denying a clean PASS: probing the closed channel is
itself signal. The receipt's `authority_resolver_config_hash` is the store's
`state_digest(evaluated_at)`, externally re-checkable with
`trusted-runtime verify-authority-digest`, which exits non-zero on any
digest that the journal fold cannot reproduce.
