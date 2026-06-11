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
- explicit enums for runtime, normative, provenance, and integrity states
- canonical receipt helpers
- formal adapter interfaces
- a golden-scenario runner
- a real EthicsCouncil hazard adapter
- a real meaning-assay adapter with translation and reconciliation

Today, the runtime can produce real council hazard review and real warrant-sidecar output from local sources. Enforcement and evidence layers remain stubbed pending adapter work.

Stubbed and unavailable layers are explicit in the contract through adapter provenance, decision integrity is classified as `FULL | PARTIAL | DEMO_ONLY`, and synthesized `PROCEED` is not allowed while required layers remain non-real.

## Package layout

```text
src/trusted_runtime/
  cli.py
  shared/
    enums.py
    models.py
    receipts.py
  integration/
    adapters.py
    engine.py
    integrity.py
    policy.py
    provenance.py
    report.py
    translation.py
examples/
  minimal_decision.py
docs/
  ARCHITECTURE.md
  CANONICALIZATION.md
  INTEGRATION_STATUS.md
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
- `EthicsCouncil`, via local source-path adapter or `ETHICS_COUNCIL_SRC`
- `meaning-assay`, via local source-path adapter or `MEANING_ASSAY_SRC`

### Still stubbed
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
