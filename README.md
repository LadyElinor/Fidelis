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
- SOPHRON-style ingestion recomputes and verifies hashes.
- Deliberately broken records fail validation.

## What this does not yet claim

- Production-grade MCP enforcement.
- Cryptographic signing.
- Full SOPHRON statistical analysis.
- Real human approval UX.
- Live database-backed telemetry.

Status: runnable minimal proof, not production infrastructure.
