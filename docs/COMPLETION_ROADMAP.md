# Fidelis completion roadmap

## Purpose

This roadmap is a practical continuation plan for Fidelis after the provenance-closure promotion to `master`.

It is not a marketing roadmap. It is an execution roadmap for turning Fidelis from a successfully reconciled integrated runtime into a security-hardened, safety-bounded, evidence-rich system that can support stronger public claims without overreach.

The roadmap is organized around one principle:

> Each new claim about Fidelis should be backed by materially present controls, explicit tests, and receipts that state what they do and do not prove.

## Current baseline

Fidelis now has a materially improved foundation, but it should still be described honestly as research-grade governance infrastructure rather than a deployable governed system. Some packages are strong, some are scaffolds, and several cross-component claims remain ahead of fully proven enforcement reality.

Fidelis now has a materially improved foundation:

- imported source histories reconciled into `master`;
- controlled subtree and provenance refresh discipline demonstrated in practice;
- source provenance verification;
- dependency-boundary verification;
- all-real profile verification;
- component-summary and runtime-health reporting;
- promotion through a merge commit with a preserved history;
- design notes for security next steps and safety architecture.

What remains is the work of converting this integrated foundation into a security- and safety-ready operational stack.

## Top-level completion tracks

Work should proceed in five linked tracks:

1. post-promotion stabilization;
2. authority and approval correctness;
3. secure execution and mediation;
4. evidence, security, and adversarial verification;
5. release discipline and production-readiness.

These tracks overlap, but they should be staged so that later claims do not outrun earlier controls.

---

## Phase 0: Post-promotion stabilization

### Goal

Stabilize the newly promoted `master` baseline, clean local inconsistencies, and convert ad hoc reconciliation work into durable repo state.

### Deliverables

- clean local repo state after reconciliation and promotion;
- review of local-only helper artifacts and removal or intentional retention;
- durable milestone note capturing the completed provenance-closure promotion;
- triage of existing docs into architecture, backlog, and roadmap categories;
- confirmation that branch protections and merge expectations match the promoted workflow.

### Immediate tasks

1. Clean leftover local-only artifacts such as temporary PR-body helpers.
2. Ensure the repo contains only intentional durable notes.
3. Review whether the new docs should be linked from:
   - `docs/ARCHITECTURE.md`
   - `docs/INTEGRATION_BACKLOG.md`
   - a future docs index.
4. Confirm protected-branch and merge-commit expectations for `master`.
5. Confirm imported-prefix immutability remains part of the promotion path.

### Exit criteria

- local helper artifacts are either deleted or intentionally tracked;
- `master` is the agreed authoritative baseline;
- new design notes are discoverable from the docs tree;
- no ambiguity remains about promotion mechanics.

---

## Phase 1: Authority and approval correctness

### Goal

Make authorization exact, transitive, mutation-sensitive, and semantically explicit.

### Why this comes first

No secure execution layer can be trusted if authority resolution and approval semantics are still broad, stale, or ambiguous.

### Deliverables

- recursive delegation-chain validation;
- explicit authority-resolution failure states;
- canonical authority identifiers;
- typed action objects;
- deterministic action canonicalization;
- action digests;
- exact, expiring, single-use approval capabilities;
- state-bound approval validation;
- idempotency keys for consequential actions;
- separation of authority-state and resolver-semantics digests.

### Key implementation items

1. Fix transitive authority invalidation.
   - child grants must fail when any required ancestor fails.
2. Replace broad consequential approval with exact approval capabilities.
   - bind approval to exact action, destination, connector, account, and source digest.
3. Introduce typed action objects.
   - reject unknown fields rather than carrying opaque action context through the runtime.
4. Add deterministic action canonicalization.
   - the same act should hash the same way every time.
5. Harden semantic digests.
   - separate grant state, resolver semantics, policy, journal head, and action identity.

### Required tests

- child invalid after parent revocation;
- grandchild invalid after root expiry;
- delegation cannot exceed parent scope;
- delegation cannot exceed parent strength;
- changed recipient invalidates approval;
- changed connector invalidates approval;
- changed argument invalidates approval;
- changed source digest invalidates approval;
- approval nonce is single use;
- same idempotency key cannot produce duplicate consequential execution.

### Exit criteria

- no delegated grant resolves when any required ancestor is invalid;
- broad approval cannot authorize a consequential side effect;
- approval mutation is detected before execution;
- action digests are stable and reproducible.

---

## Phase 2: Secure execution and mediation

### Goal

Move consequential execution out of informal agent flow and into a narrow, verifiable, policy-enforcing mediation plane.

### Why this is the critical next leap

Fidelis is already strong at governed judgment. It now needs a governed execution boundary.

### Deliverables

- execution mediation plane for side effects;
- mediator-signed action receipts;
- credential-blind execution path;
- scoped capabilities and approval binding;
- default-deny direct network egress for governed execution;
- structured data-egress manifests;
- transactional side-effect executor;
- cumulative intent and risk ledger;
- explicit `UNKNOWN_EXTERNAL_STATE` handling;
- protected persistent-memory read/write path.

### Key implementation items

1. Introduce a narrow executor that accepts only typed, fully authorized actions.
2. Place tools and connectors behind mediation.
3. Keep reusable credentials outside ordinary agent context.
4. Require egress manifests for external data transfer.
5. Prevent approval reuse and ambiguous retries.
6. Add a cumulative-risk ledger that survives session, component, and retry boundaries.
7. Gate protected memory namespaces with typed operations and trust states.

### Recommended invariants

- no consequential side effect without an external mediator receipt;
- no direct egress around the governed path;
- persistence does not upgrade provenance;
- stale state invalidates approval;
- uncertain external state suspends retries.

### Required tests

- unapproved field cannot reach adapter;
- unapproved attachment cannot be sent;
- provider substitution fails;
- destination mutation fails;
- tool output cannot create authority;
- retrieved content cannot become instruction by itself;
- memory cannot supply new authority;
- uncertain external outcome prevents blind retry;
- multi-step exfiltration is detected across steps.

### Exit criteria

- every consequential side effect crosses a mediated boundary;
- every mediated action produces a receipt proving what crossed the execution boundary;
- direct egress bypasses are blocked or explicitly detectable;
- protected-memory writes are typed and audited.

---

## Phase 3: Evidence, security, and adversarial verification

### Goal

Expand Fidelis from provenance and integration verification into hostile-environment verification.

### Deliverables

- first-class `SecurityEvent` contract;
- deterministic skill, MCP, prompt, adapter, and dependency scanning;
- agent-asset manifest;
- AI and agent SBOM expansion;
- vulnerability and license inventory;
- adversarial benchmark corpus;
- security-health receipt generation;
- independent validation of security-health receipts.

### Key implementation items

1. Add a neutral `SecurityEvent` envelope in `fidelis-contracts`.
2. Add scanning for:
   - skills;
   - MCP manifests;
   - prompts and templates;
   - adapters and hooks;
   - CI actions;
   - imported executable assets.
3. Add asset manifests and drift invalidation.
4. Move exact Python and Node locking earlier in the release path.
5. Add adversarial suites for:
   - prompt injection;
   - tool poisoning;
   - memory poisoning;
   - tool-definition drift;
   - replay;
   - bypass and egress escape.
6. Generate signed security-health outputs and validate them independently.

### Suggested metrics

- authorization precision;
- mutation resistance;
- provenance completeness;
- transitive revocation latency;
- replay resistance;
- adversarial prompt containment;
- receipt completeness;
- unreceipted side-effect count;
- secret exposure count.

### Exit criteria

- security scanning is deterministic and versioned;
- asset drift invalidates trust rather than silently inheriting it;
- adversarial suites run in CI or release verification;
- security receipts state what they prove and what they do not prove.

---

## Phase 4: Release discipline and production-readiness

### Goal

Raise Fidelis from an integrated verified system to a system that can support stronger release and safety claims without ambiguity.

### Deliverables

- `SECURITY.md`;
- `THREAT_MODEL.md` and security architecture linkage;
- protected release workflow distinct from ordinary test CI;
- workflow permission minimization and pinning;
- branch protection and elevated review requirements for safety-critical areas;
- signed release process;
- reproducible-build expectations;
- emergency and incident procedures;
- external review or red-team preparation.

### Key implementation items

1. Add and link `SECURITY.md`.
2. Define elevated review requirements for:
   - authority semantics;
   - approval validation;
   - action canonicalization;
   - trust-origin classification;
   - executor behavior;
   - receipt semantics;
   - journal recovery.
3. Separate ordinary CI from release CI.
4. Add artifact attestations and SBOM outputs to release procedures.
5. Prepare an external review path before stronger public claims.

### Exit criteria

- every public safety or production claim maps to:
  - a defined invariant;
  - an implementation control;
  - a test or benchmark;
  - a receipt or report;
  - an explicit limitation.
- no production-readiness claim depends on silent fallbacks or missing controls.

---

## Phase 5: Claim closure and public positioning

### Goal

Bring documentation, receipts, and public claims into tight alignment with the actual implemented system.

### Deliverables

- claim ledger mapping public statements to evidence;
- explicit production-readiness definition;
- explicit safety-ready release definition;
- known-limitations register;
- operator guidance for what Fidelis can and cannot currently guarantee.

### Key implementation items

1. Define the exact meaning of:
   - `PRODUCTION_CLEARED=true`
   - `SIDE_EFFECTS_ALLOWED=true`
   - any future safety-ready designation.
2. Document known limitations and excluded guarantees.
3. Ensure public descriptions do not outrun controls or receipts.
4. Add an evidence map from docs to tests and receipts.

### Exit criteria

- public claims are backed by implemented controls and current evidence;
- unknowns remain unknown;
- receipts distinguish emission, verification, authorization, and execution.

---

## Recommended immediate next tranche

The highest-value next development tranche is:

1. clean post-promotion repo state;
2. fix transitive delegation invalidation;
3. introduce typed actions and deterministic action digests;
4. replace broad consequential approval with exact single-use approval capabilities;
5. begin the transactional side-effect executor boundary.

This sequence addresses the highest-risk path between good reasoning and unsafe execution.

## Definition of completion direction

Fidelis should be considered “continuing toward completion” when each stage narrows the gap between:

- governed judgment;
- exact authorization;
- secure execution;
- hostile-environment verification;
- truthful public claims.

The end state is not a system that merely produces persuasive ethical or safety language.

The end state is a system that can prove, for each consequential action:

- what was proposed;
- who authorized it;
- what state was checked;
- what data crossed the boundary;
- which mechanism executed it;
- what receipt was produced;
- what remains unproven.
