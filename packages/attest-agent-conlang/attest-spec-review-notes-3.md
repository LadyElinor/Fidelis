# Attest Spec Review Notes 3 (2026-06-29)

This review was performed against the actual `attest-spec.md` artifact rather than prior review-note summaries.

## Epistemic status

This pass is still from inside the same ancestry line and therefore is not independent validation. Treat it as adversarial editing, not certification. Two independent checks still missing are:
- a different model family red-teaming the soft layer
- a mechanical verifier harness that executes the hard layer without a model in the loop

## Fidelity check

Confirmed against `attest-spec.md`:
- canonicalization is a stated correctness requirement (§10)
- `ENDORSE` exists with a warrant ceiling (§6.1, §13.3)
- `RETRACT` has append-only tombstone semantics (§18)
- `ordering_anchor` is required and identity-bearing (§9.1)
- the hard/soft split is wired through §15

The prior summaries were faithful on those points.

## Concrete correctness defects

### 1. `handled_by` is load-bearing but not hashed

Problem:
- §9.1 requires a `handled_by` relay/processor trail
- §10.2 defines the exact identity-bearing field set and omits `handled_by`
- therefore handler-trail mutation is not identity-visible

Consequence:
- contradicts §9.2 relay-mutation detection and §10.4 relay accountability
- deeper issue: an append-only mutable handler list conflicts with content-addressing anyway

Recommended fix:
- remove `handled_by` as a first-class field
- model every handoff as an immutable `RELAY` message
- reconstruct handler trail from the parent DAG instead

### 2. Warrant-bearing frames are underspecified

Problem:
- §8 says assertions and hypotheses must include a warrant
- §8.5 only names `ASSERT` and `HYPOTHESIZE`
- but the spec functionally uses warrants on `ENDORSE`, `DISSENT`, `RETRACT`, and `COMMIT`

Consequence:
- malformedness hole for evidential warrants on those other frames without grounds
- `ENDORSE` upgrades are partly covered in §13.3, but non-upgrading evidential misuse is not

Recommended fix:
- enumerate all warrant-bearing frames in §8
- extend the grounds-required rule to all warrant-bearing frames carrying evidential warrant types

### 3. Origin attribution is only hard when signatures are present

Problem:
- §10.3 makes signatures optional
- §15.2 verifies signatures only when present
- unsigned `from` values are only self-declared origin labels bound into a hash

Consequence:
- unsigned messages are tamper-evident relative to a claimed origin, not origin-authenticated

Recommended fix:
- require signatures for any non-`RELAY` frame whose warrant others are expected to rely on
- otherwise state the limit explicitly in the default profile

## Hard/soft boundary corrections

### ENDORSE ceiling buys less than optimistic summaries imply

Hard gain actually present:
- trivial laundering with no new grounds becomes malformed or hard-failing

What remains soft:
- correlated-but-not-independent new grounds
- sufficiency of new grounds
- independence-breaking transformation predicate

Conclusion:
- the ceiling is still useful, but only blocks the crude class of laundering in v0.1/v0.2

### Retract conflict is hard only in ancestry-reachable cases

Problem:
- §18.3 relies on ordering anchor precedence to decide retract-vs-aggregate conflict
- adversarial case is causal concurrency, where retract and aggregate are not in one another's ancestry

Conclusion:
- if retract is reachable in ancestry, conflict is decidable from parent structure and mostly trivial
- if retract is concurrent, anchor ordering is advisory rather than a hard check

Recommended fix:
- split reachable-ancestry retract checks from concurrent retract conflicts

### Dissent preservation is meaningfully semantic

Problem:
- carrying the dissent ID is hard-checkable
- carrying its meaning faithfully is semantic and soft
- opaque aggregates cannot make the strong semantic version hard

Conclusion:
- visibility upgrades ID-presence checks, not faithful dissent preservation
- the meaningful property remains soft

## First-class ceiling worth stating explicitly

Recommended protocol-level scope statement:
- content-addressing certifies positive artifact-local properties
- negative or closure properties require a known-complete source set
- no wire format can guarantee completeness of unseen material

This ceiling governs:
- dissent preservation
- retract propagation
- independence claims

## Trust-precondition note

The hard layer is only hard relative to the integrity of the artifact-resolution substrate.

If grounds resolve against a forgeable receipt store, then resolution can pass on fabricated artifacts. Attest therefore inherits the trust properties of its receipt root or execution substrate rather than establishing them from scratch.

## Warrant lattice criticism

Problem:
- §8.2.1 fixes a single total warrant order as compatibility-defining
- some order relations are deployment-contestable
- the most privileged class may ride on the most forgeable substrate

Recommended fix:
- make the warrant order a declared deployment lattice
- keep the current ordering as the default profile, not the only compatible one

## Bottom line

Attest's hard additions are real and useful:
- closed typed illocution set
- mandatory warrant-with-grounds presence
- lineage for declared ancestry overlap

But most motivating trust-failure targets remain conditional or soft:
- injection becomes attributable, not prevented
- independence remains only partly checkable
- dissent preservation is semantic and completeness-conditional
- provenance gives integrity of declared form, not truth

One upstream narrative risk remains:
- `attest.txt` still appears to overclaim in ways the spec text itself has already narrowed
- the pitch materials should be reconciled to the spec's more honest scope language before reuse
