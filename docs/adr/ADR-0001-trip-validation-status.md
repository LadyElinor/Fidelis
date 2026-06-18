# ADR-0001: Trip validation status is executable, not merely documentary

## Status
Accepted

## Context
TrustedRuntime integrates multiple upstream safety and governance layers whose maturity is uneven. Some tripwires are runtime policy invariants, while others are heuristic detectors still being calibrated in their home repos.

Without an explicit executable status model, unvalidated or calibrating tripwires can be silently consumed downstream as if they were validated blockers.

## Decision
TrustedRuntime will surface an explicit `TripValidationStatus` enum with the statuses:
- `UNVALIDATED`
- `CALIBRATING`
- `VALIDATED`
- `RETIRED`

TrustedRuntime decisions will include typed `tripwire_records` declaring:
- tripwire id
- source layer
- status
- rationale
- whether the tripwire is allowed for blocking use
- whether the tripwire is allowed for advisory use

Runtime policy will treat any tripwire marked for blocking use as ineligible to support `PROCEED` unless its status is `VALIDATED`.

## Consequences
Positive:
- downstream consumers can no longer confuse calibration state with production trust
- trip maturity becomes receipt-visible and testable
- governance upgrades can happen incrementally without narrative ambiguity

Negative:
- more explicit metadata must be maintained
- some previously implicit assumptions are now downgraded into explicit advisory-only status
