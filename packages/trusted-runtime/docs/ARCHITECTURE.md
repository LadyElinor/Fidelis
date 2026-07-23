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
- formal adapter interfaces
- canonical receipt hashing rules
- decision integrity classification
- pipeline assembly
- reconciliation-aware report synthesis

## Non-goals

TrustedRuntime should not absorb the logic of the independent layers.
Its job is orchestration, contract discipline, and synthesis.

## Current state
- Real local EthicsCouncil adapter
- Real local meaning-assay adapter
- ProposedAction to meaning-assay case translation
- Reconcile-based synthesis using `meaning_assay.bridge`
- Stubbed enforcement and evidence layers

## Immediate next integrations
1. TrustworthyAgentStack adapter
2. CER/SOPHRON adapter
3. richer arbitrary-action to meaning-assay case synthesis beyond heuristic mapping
