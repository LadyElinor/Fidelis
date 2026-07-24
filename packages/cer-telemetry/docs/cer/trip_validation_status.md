# CER trip validation status

This repo distinguishes between tripwire maturity states:

- `UNVALIDATED`
- `CALIBRATING`
- `VALIDATED`
- `RETIRED`

## Current policy
Measurement and provenance invariants are treated as hardened enforcement surfaces.
Safety invariants remain calibration-era signals unless explicitly promoted.

## Current mapping
- measurement invariants: `VALIDATED` for fail-on-violation semantics inside this repo's current contract
- provenance invariants: `VALIDATED` for fail-on-violation semantics inside this repo's current contract
- safety invariants: `CALIBRATING` by default

## Consumption rule
A tripwire that is not `VALIDATED` may remain visible and advisory, but must not silently impersonate a trusted blocking detector in downstream systems.

## Promotion rule
Promotion from `CALIBRATING` to `VALIDATED` should require:
- explicit benchmark/corpus criteria
- declared failure modes
- reproducible validation artifact references
- documented decision record for the promotion
