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
- `src/trusted_runtime/integration/attest_bridge.py` exists as a concrete design stub,
- `assemble_execution_decision()` now records an Attest-shaped ingress message,
- the bridge emits explicit process provenance,
- report rendering now surfaces bridge presence and verification status,
- the pytest module `tests/test_attest_bridge.py` covers the first contract invariants,
- and a real `AttestAgentConlang` import/wiring path now exists behind an availability gate.

This is still **not** yet a full all-real end-to-end Attest runtime.
Current behavior is:
- when `AttestAgentConlang` is importable, the bridge can run real verifier calls for the bridged message surface,
- when it is unavailable, the bridge falls back truthfully to `UNVERIFIABLE` stub mode rather than pretending success.

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

## Non-claims

This seam should not be overstated.
Current work does **not** claim:
- full direct AttestAgentConlang runtime import/wiring,
- transitive grounds-cycle closure beyond current Attest behavior,
- full signer cryptography,
- or complete all-real end-to-end deployment.

## Files

- `src/trusted_runtime/integration/attest_bridge.py`
- `docs/attest_bridge_test_plan.md`
- `tests/test_attest_bridge.py`
