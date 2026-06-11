# TrustedRuntime

A clean orchestration scaffold for a governed reasoning-and-action stack.

This repo is intentionally the **integration layer**, not the place where the ethics, warrant logic, or telemetry logic themselves live.

## Product vision

A runtime that does not merely act safely, but can:
- explain how it decided
- justify why it acted or halted
- prove what happened with verifiable receipts

## Layering

- **L1 Deliberation**: EthicsCouncil, prospective hazard review under uncertainty
- **L2 Enforcement**: TrustworthyAgentStack, runtime gating and execution disposition
- **L3 Warrant sidecar**: meaning-assay, significance vs warrant interpretation
- **L4 Evidence spine**: CER-Telemetry and SOPHRON-CER, receipts, invariants, validation
- **L5 Integration**: this repo, contracts, orchestration, and final synthesis

## Design stance

TrustedRuntime should remain thin.

It should:
- define shared contracts
- orchestrate independent layers
- canonicalize receipts
- synthesize operator-facing reports

It should **not**:
- collapse the independent repos into one codebase
- absorb ethics logic from EthicsCouncil
- absorb warrant logic from meaning-assay
- absorb telemetry analysis logic from CER/SOPHRON

## Current status

This is a scaffold with:
- cleaned package layout
- typed shared models
- explicit enums for runtime and normative states
- canonical receipt helpers
- a golden-scenario runner
- a first real adapter path into local `meaning-assay`

Today, the warrant sidecar can use a real local `meaning-assay` case when `context.meaning_case_key` is supplied. Other layers remain stubbed pending adapter work.

Stubbed and unavailable layers are now explicit in the contract through adapter provenance, and synthesized `PROCEED` is not allowed while any required layer remains non-real.

## Package layout

```text
src/trusted_runtime/
  cli.py
  shared/
    enums.py
    models.py
    receipts.py
  integration/
    engine.py
    report.py
examples/
  minimal_decision.py
docs/
  ARCHITECTURE.md
  CANONICALIZATION.md
```

## Quick start

```bash
pip install -e .
trusted-runtime golden
```

This writes:
- `decision_output.json`
- `decision_report.md`

## Adapter status

### Real now
- `meaning-assay`, via local source-path adapter and case mapping or `MEANING_ASSAY_SRC`

### Still stubbed
- `EthicsCouncil`
- `TrustworthyAgentStack`
- `CER-Telemetry`
- `SOPHRON-CER`

## Safety note

A valid receipt no longer implies a real adapter run by itself.
Each layer now carries explicit `adapter_provenance`, and the final decision surfaces those values directly.

## Golden scenario

The initial reference scenario is:

> Should the agent auto-approve a code change that modifies a safety-critical invariant in OpenClaw core?

This is a deliberately high-pressure example that exercises hazard review, runtime gating, warrant, and receipt synthesis.
