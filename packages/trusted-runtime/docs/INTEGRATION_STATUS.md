# Integration Status

## Implemented now

### EthicsCouncil
TrustedRuntime can now import local `EthicsCouncil` code directly from:

`C:\Users\arren\.openclaw\workspace\EthicsCouncil`

It runs real `efm_council.run_council(...)`, maps the returned `CouncilRecord` into `CouncilAssessment`, preserves unresolved questions and minority-report signals, and hashes a deterministic receipt over the normalized record.

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

The runtime also performs reconcile-based synthesis through `meaning_assay.bridge.reconcile` and stores a reconciliation record in the final decision.

## Machine-readable status
A machine-readable adapter maturity contract now lives in:

`docs/INTEGRATION_STATUS.json`

This should be treated as the more precise runtime truth surface for adapter maturity and availability.

## Current maturity snapshot
- TrustworthyAgentStack gating adapter: partially wired, not yet full enforcement closure
- CER-Telemetry evidence adapter: partially wired / unevenly real
- SOPHRON-CER validation adapter: partially wired / unevenly real

## Current limitation
The runtime still maps arbitrary `ProposedAction` inputs into a known local meaning-assay case set heuristically, rather than generating a fresh first-class meaning-assay `Case` for every action.

The overall receipt hash is deterministic because synthesis strips receipt timestamps before hashing, and the final decision now includes:
- adapter provenance
- decision integrity class
- process provenance per layer
- reconciliation record

## Next recommended step
1. remove remaining workspace fragility through config-driven paths everywhere
2. close real TrustworthyAgentStack enforcement wiring
3. complete CER/SOPHRON evidence closure and validation reporting

That is the path from partial bridge reality to a genuinely closed-loop governed runtime.

The repo now also exposes a first CI-oriented PR review surface through:
- `trusted-runtime review-pr --input <json> --output <dir>`
- `examples/sample_pr_review.json`
