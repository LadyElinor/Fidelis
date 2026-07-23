# ADR-0003: Currency splits into evidence freshness and baseline freshness

## Status
Accepted

## Context
A single notion of currency hides two distinct failure modes:
1. evidence for a decision may be stale
2. the detector or baseline distribution used to interpret the evidence may itself be stale

These failures should not be collapsed.

## Decision
TrustedRuntime and its adjacent telemetry/governance stack should treat currency as two separate concerns:
- evidence freshness
- baseline freshness

Telemetry and drift-monitoring layers should surface stale baselines explicitly rather than treating them as merely weak evidence.

## Consequences
- stale detector baselines become visible governance events
- evidence staleness and calibration staleness can be remediated separately
- future policy can gate on either or both forms of currency failure
