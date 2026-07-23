# All-Real Setup Guide

This guide explains how to reach TrustedRuntime's **all-real** profile in a local workspace.

It is intentionally contributor-facing and conservative.

## What "all-real" means

`all-real` is a **computed local runtime condition**, not a marketing label and not a published release guarantee.

TrustedRuntime treats a layer as meaningfully real only when required surfaces are simultaneously:

- **import-real**: live integration code can be imported
- **path-real**: required repos/files/entrypoints exist at resolved paths
- **behavior-real**: the runtime actually exercises the live path rather than a fallback

See also: `docs/ALL_REAL_PROFILE_CONTRACT.md`

## Required local sibling surfaces

TrustedRuntime currently computes `all-real` across these required layers:

- **L1** EthicsCouncil
- **L2** TrustworthyAgentStack
- **L3** meaning-assay
- **L4** SOPHRON-CER / CER telemetry closure
- **Bridge** AttestAgentConlang seam availability

If any required layer is missing or degrades to non-behavior-real, the detected mode should fall back to `partial` or `stub`.

## Workspace expectations

By default, TrustedRuntime resolves sibling paths relative to `TRUSTED_RUNTIME_WORKSPACE_ROOT` or the enclosing workspace layout.

You can either:

- use the default local workspace layout expected by `src/trusted_runtime/config.py`, or
- set explicit environment variables for sibling repos

Useful variables include:

- `TRUSTED_RUNTIME_WORKSPACE_ROOT`
- `MEANING_ASSAY_SRC`
- `ETHICS_COUNCIL_SRC`
- `TRUSTWORTHY_AGENT_STACK_SRC`
- `SOPHRON_CER_SRC`
- `ATTEST_AGENT_CONLANG_SRC`

## Attest bridge verifier mode

TrustedRuntime's Attest seam now has an explicit verifier-mode truth surface.

Current bridge modes are:

- `accept-all`
- `deterministic-test`
- `ed25519-profile`

Important caveat:

- selecting `ed25519-profile` does **not** by itself prove strong signature verification
- the loaded Attest deployment profile must actually provide signer keys
- at the time of writing, the default sibling profile may legitimately contain an empty `signer_public_keys` map, which means this path should not be overread as a strong passing configuration

## Quick local activation

Example shell setup:

```bash
export TRUSTED_RUNTIME_WORKSPACE_ROOT=~/openclaw/workspace
pip install -e .
trusted-runtime health
trusted-runtime live-stack-smoke --input examples/ai_agent_shell_access.json --output .ci-artifacts --require-all-real
```

## What success looks like

A truthful local all-real run should show:

- `integration_mode` computed as `all-real`
- `integration_mode_report.mode == "all-real"`
- required components with `behavior_real: true`
- smoke artifact with `truthfulness_gate_passed: true`
- no fake `REAL` provenance on degraded paths

It should **not** imply:

- a published reproducible release artifact
- complete L2 or L4 closure beyond what current receipts and tests prove
- security-bearing Attest/CER semantics beyond the currently implemented verifier path

## Verification workflow

Recommended checks:

```bash
trusted-runtime health
trusted-runtime live-stack-smoke --input examples/ai_agent_shell_access.json --output .ci-artifacts --require-all-real
python -m pytest -q
```

Inspect these outputs:

- `.ci-artifacts/live_stack_smoke.json`
- `.ci-artifacts/smoke_decision_output.json`
- `.ci-artifacts/smoke_decision_report.md`

In `smoke_decision_report.md`, the **CER verifier provenance** block now surfaces the bridge-derived verifier metadata that actually reached the CER bundle, including:

- `evaluated_at`
- `profile_hash`
- `known_message_set_hash`
- `signature_verifier_identity`
- `verifier_hash`
- `resolver_config_hash`

Interpretation rule:

- these fields prove which verifier/config surface the runtime actually serialized into CER-facing decision artifacts
- they do **not** by themselves prove that the underlying verifier result was a strong security PASS, nor that artifact-backing, authority semantics, replay resistance, or full closure claims were satisfied

The machine-readable decision export is shaped through:

- `src/trusted_runtime/export.py`

## Layer diagram

```text
TrustedRuntime (orchestration + policy)
├── L1 EthicsCouncil
├── L2 TrustworthyAgentStack (closure bar + checkpoints)
├── L3 meaning-assay
├── L4 SOPHRON-CER / CER telemetry
└── AttestAgentConlang bridge seam
    ↓
ExecutionDecision
├── integration_mode_report
├── cer_bundle.sophron_validation
└── cer_bundle.cer_enrichment
```

## Current truth boundary

Today, `all-real` is best understood as:

- a locally achieved computed runtime profile
- guarded by explicit truthfulness checks
- useful for contributor verification and CI smoke enforcement
- not yet a portable release claim
