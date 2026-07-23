# ADR-0004: Validated vs unvalidated tripwires have different gate semantics

## Status
Accepted

## Context
The stack contains both hard policy invariants and heuristic detector outputs. Treating them as interchangeable causes governance drift.

## Decision
Tripwires marked:
- `VALIDATED` may be used for blocking gate semantics when policy permits
- `UNVALIDATED`, `CALIBRATING`, and `RETIRED` may remain advisory but must not silently function as trusted blockers

TrustedRuntime will explicitly downgrade `PROCEED` when a blocking tripwire is not `VALIDATED`.

## Consequences
- policy semantics become executable instead of aspirational
- advisory safety signals remain visible without impersonating hardened gates
- future promotion from advisory to blocking requires explicit validation work
