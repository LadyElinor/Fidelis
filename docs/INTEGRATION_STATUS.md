# Integration Status

## Implemented now

### meaning-assay
TrustedRuntime can now import local `meaning-assay` code directly from:

`C:\Users\arren\.openclaw\workspace\27assay\meaning-assay\src`

When `ProposedAction.context.meaning_case_key` is present, the runtime:
- resolves that case from `meaning_assay.cases`
- runs real `analyze(case)`
- captures the real meaning-assay receipt
- maps the resulting quadrant into `NormativeSummary`
- stores the originating case key in `pair_contrasts.source_case`
- marks the layer `adapter_provenance=REAL`

When the adapter is unavailable or unmapped, the runtime falls back explicitly to `adapter_provenance=STUB` instead of silently implying parity with the real path.

This is the first non-stubbed external layer in the stack.

## Still stubbed
- EthicsCouncil hazard adapter
- TrustworthyAgentStack gating adapter
- CER-Telemetry evidence adapter
- SOPHRON-CER validation adapter

## Current limitation
The runtime currently maps a pre-existing local meaning-assay case rather than synthesizing a new case from arbitrary `ProposedAction` content.

The overall receipt hash is now made deterministic by stripping receipt timestamps from the synthesis payload before hashing.

That is acceptable for this stage because it proves:
- real package import
- real analysis invocation
- real receipt flow
- contract compatibility under non-fake output

## Next recommended step
Implement the real EthicsCouncil adapter next.
That would make both:
- prospective hazard review
- normative warrant interpretation

external and real, leaving only enforcement and evidence stubs.
