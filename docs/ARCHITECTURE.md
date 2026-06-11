# TrustedRuntime Architecture

TrustedRuntime is the thin orchestration layer for a governed reasoning-and-action stack.

## Layering

### L1 Deliberation
EthicsCouncil performs prospective hazard review under uncertainty.
Its output should remain distinct from normative warrant.

### L2 Enforcement
TrustworthyAgentStack turns upstream judgments into real runtime branches:
- proceed
- halt
- confirm human
- suspend

### L3 Warrant sidecar
meaning-assay interprets the proposed or executed act in terms of:
- significance
- warrant
- normative summary / quadrant
- failure modes

### L4 Evidence spine
CER-Telemetry and SOPHRON-CER preserve:
- receipts
- invariants
- provenance
- validation
- drift visibility

### L5 Integration
TrustedRuntime defines:
- shared contracts
- canonical receipt hashing rules
- pipeline assembly
- operator-facing report synthesis

## Non-goals

TrustedRuntime should not absorb the logic of the independent layers.
Its job is orchestration, contract discipline, and synthesis.

## Recommended real-integration order
1. meaning-assay adapter
2. EthicsCouncil adapter
3. TrustworthyAgentStack adapter
4. CER/SOPHRON adapter
