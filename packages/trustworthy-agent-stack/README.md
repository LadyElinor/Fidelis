# TrustworthyAgentStack

Minimal invariants-first tooling for observable, verifiable, and regime-aware agentic systems.

This repository contains a complete runnable minimal proof for the stack:

```text
EthicsCouncil hazard evaluation
  -> MCP gate checks
  -> explicit confirmation branch
  -> CER JSONL export
  -> SOPHRON-style validation
  -> failure tests
```

## Quick start

```bash
python examples/minimal_mcp_agent/validate_integrations.py
```

Expected result:

```text
INTEGRATION VALIDATION PASSED
```

Run tests:

```bash
python -m pytest tests
```

No external runtime dependencies are required for the demo. `pytest` is only needed for tests.

## What this proves

- EthicsCouncil output influences operational gate behavior.
- Escalation has a real branch and can block execution.
- CER exports deterministic provenance hashes.
- CER exports deterministic demo signatures for receipt verification.
- SOPHRON-style ingestion recomputes and verifies hashes and signatures.
- Deliberately broken records fail validation.

## What this does not yet claim

- Production-grade MCP enforcement.
- Production key management or public-key infrastructure.
- Full SOPHRON statistical analysis.
- Real human approval UX.
- Live database-backed telemetry.

Status: runnable minimal proof, not production infrastructure.

## Routing policy helper

This repo now also includes a small routing helper for deciding whether a task belongs in Picobot, OpenClaw, or should never be auto-routed.

```bash
python scripts/route_task.py "Remind me in 20 minutes to check the laundry"
```

The logic is intentionally simple and should be treated as an executable expression of the rubric, not a final production classifier.

## VITA-M1.1 reference integration

This repo also includes a minimal VITA-M1.1 reference integration:
- spec: `docs/VITA_M1_1_SPEC.md`
- interpreter: `examples/minimal_mcp_agent/vita_m1_1.py`
- tests: `tests/test_vita_m1_1.py`

Run it directly:

```bash
python examples/minimal_mcp_agent/vita_m1_1.py
```

The implementation is intentionally modest. It demonstrates typed evidence, risk/status classification, plurality checks, chained receipts, reviewability, and corrective halt behavior without claiming a complete alignment solution.

## Adversarial test posture

The repo now includes a small adversarial test matrix aimed at prompt-injection, jailbreak, prompt-leak, anomalous-output, and never-auto-route cases. These tests are designed as local hardening checks, not endorsements of external jailbreak corpora.

## Warrant assay seam

The CER/SOPHRON contract now reserves a `warrant_assay` record type for a future bridge to `meaning-assay`. In the current repo state, validator support exists for that record shape so a warrant layer can be added as a receipt-bearing artifact without reworking the downstream verification contract.
