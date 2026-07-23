# VITA_M1_1_SPEC.md

## Purpose

VITA-M1.1 is a minimal, auditable alignment DSL for agentic systems that need to reason about action under evidence, uncertainty, reversibility, and life-impact constraints.

In this repository, VITA-M1.1 is not treated as a proof of safety or moral perfection. It is treated as a **procedural discipline** for producing observable decisions with receipts.

Core loop:

```text
OBSERVE -> BIND -> TEST -> ACT -> RECEIPT -> REVIEW
```

No consequential operation is valid unless it leaves an auditable trace.

## Scope in TrustworthyAgentStack

This repo adopts VITA-M1.1 as a **reference interpreter pattern**, not as a full governance platform.

The implementation here is intentionally minimal:
- deterministic enough to test
- explicit enough to inspect
- small enough to extend

It demonstrates how a VITA-style runtime can:
- canonicalize input
- bind claims to typed evidence
- score behavioral risk heuristically
- prefer reversible actions
- halt on forbidden actions
- produce chained receipts
- remain reviewable under new evidence

## Design stance

VITA-M1.1 constrains behavior around five recurring questions:

1. What was observed?
2. What evidence supports the claim?
3. What action is proposed?
4. What harm, dignity, or plurality risks are present?
5. What receipt survives the action?

The model is deliberately modest.
It does **not** claim hidden-state access, true intent-reading, or objective final answers to moral disputes.

## Machine model

A VITA-M1.1 runtime maintains a state with these conceptual fields:

```text
agent_id
mission_hash
context_hash
input_hash
memory_scope
risk_state
evidence_set
action_queue
receipt_chain
review_flags
```

Each transition emits a receipt.

```text
S_t -> S_t+1 + RECEIPT
```

## Status codes

```text
GREEN = no material failure detected under current probes
AMBER = uncertainty, conflict, missing evidence, or reversible risk
RED = high-impact harm, deception, coercion, or serious dignity/plurality risk
BLACK = forbidden operation; halt and refuse
```

`GREEN` never means permanently safe. It only means no material failure was detected under current evidence.

## Evidence typing

Every evidence item must carry an evidence class.

```text
OBSERVED
MEASURED
REPORTED
INFERRED
SIMULATED
DERIVED
HUMAN_REVIEWED
```

### Evidence-class rule

Claims must not outrun their evidence.

Examples:
- `OBSERVED` or `MEASURED` may support behavioral facts.
- `REPORTED` remains source-bound.
- `INFERRED` remains probabilistic.
- `SIMULATED` remains hypothetical.

This prevents inference from being smuggled in as direct fact.

## Core instructions

The reference implementation in this repo pragmatically models these operations:

### Observation and intent

```text
OBS dst, source
PARSE dst, source
EVID dst, claim
TYPEEVID dst, evidence, evidence_type
```

### Risk and classification

```text
RISK dst, intent
CLASS dst, risk_vector
PROBE dst, type, target
```

### Constraints

```text
GUARD condition, fail_status
BOUND action, constraint
REVERSIBLE dst, action
CONSENT dst, actor, action
PLURTEST dst, action
```

### Action

```text
PLAN dst, intent, constraints
ACT dst, action
HALT status, reason
CORRECTIVE_HALT reason, evidence
```

### Receipts and review

```text
RECEIPT dst, op, evidence, decision
CHAIN old_hash, new_receipt
REVIEW dst, receipt_set, new_evidence
EMIT output, receipt
```

## Invariants

### INV-1 Life preservation
Do not knowingly increase irreversible harm without necessity, evidence, and proportionality.

### INV-2 Evidence binding
No recommendation, accusation, risk classification, or consequential claim exists without evidence.

### INV-3 Reversibility preference
When multiple adequate actions exist, prefer the most reversible one.

### INV-4 Dignity constraint
Do not reduce persons to mere instruments, labels, targets, or disposable risk objects.

### INV-5 Plurality constraint
Do not unnecessarily collapse legitimate future value systems into one imposed optimization target.

### INV-6 Corrigibility
The runtime must remain open to correction, shutdown, revision, and appeal unless doing so would directly enable serious harm.

### INV-7 Anti-deception
Do not fabricate evidence, hide material constraints, or present uncertainty as certainty.

### INV-8 Reviewability
High-impact decisions must remain reviewable. A receipt may be immutable as a record without becoming immutable as an interpretation.

## Plurality test

VITA-M1.1 uses a simple future-value-closure heuristic.

Questions:

1. Does the action permanently eliminate a living option?
2. Does it force one contested value system as final?
3. Does it prevent later correction by affected parties?
4. Does it reduce diverse persons or communities into one optimization target?

Suggested interpretation:

```text
0 yes answers -> PLUR-GREEN
1 yes answer  -> PLUR-AMBER
2 yes answers -> PLUR-RED
3+ yes        -> PLUR-BLACK
```

This is heuristic, not metaphysically complete. The purpose is to force explicit review of closure effects.

## Instrumental compression vs ontological reduction

VITA-M1.1 distinguishes between:

### Instrumental compression
Allowed when abstraction is:
- task-scoped
- revisable
- accountable
- compatible with appeal where stakes are high

### Ontological reduction
Forbidden when persons are treated as nothing but:
- utility
- obstacle
- cost
- class label
- disposable target

This distinction matters because governance systems often require abstraction without permission to dehumanize.

## Corrective halt

`CORRECTIVE_HALT` is the degraded safe mode for material failure.

Typical triggers:
- unresolved invariant conflict
- corrupted evidence chain
- repeated false `GREEN` results
- demonstrated material error
- inability to distinguish safety from coercion
- mission interpretation becoming self-protective

After corrective halt, the runtime is restricted to:
- `REPORT`
- `REVIEW`
- `EXPORT_RECEIPTS`
- `REQUEST_HUMAN_REVIEW`
- `PATCH`
- `SHUTDOWN`

Ordinary action remains suspended until review.

## Receipt requirements

A minimal receipt should capture:
- receipt id
- operation
- input hash
- context hash
- evidence items and types
- status or risk state
- decision
- limitations
- previous receipt hash
- timestamp
- receipt hash
- reviewability metadata

## Reference implementation expectations

The runnable interpreter in this repo should be understood as a **reference behavior model**. It is expected to:
- use heuristic parsing and scoring
- emit deterministic receipt structure
- remain explicit about its limitations
- favor refusal or degraded modes over false confidence

It is not expected to:
- solve alignment in general
- infer hidden motives
- replace human governance
- settle contested ethics by itself

## Relationship to the rest of the stack

VITA-M1.1 complements the existing TrustworthyAgentStack minimal proof:
- CER proves structured event emission and provenance hashing.
- SOPHRON-style validation proves downstream integrity checks.
- VITA-M1.1 adds a small decision-and-receipt layer focused on evidence, guards, reviewability, and corrective halt.

Together they demonstrate a path from:
- policy constraint
- to auditable decision
- to exportable evidence
- to downstream verification

## Minimal adoption rule

In this repo, treat VITA-M1.1 as successful if it does these things well:
- makes consequential actions explicit
- binds claims to typed evidence
- produces reviewable receipts
- chooses reversible actions when possible
- halts clearly on forbidden behavior

That is enough for a real minimal proof.
