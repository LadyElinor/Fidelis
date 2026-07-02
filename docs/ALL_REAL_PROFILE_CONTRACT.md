# All-Real Profile Contract

## Definition

All-Real means all required runtime layers are simultaneously:
- **import-real**: the runtime can import the required live integration surface
- **path-real**: the required repo/files/entrypoints are present at resolved paths
- **behavior-real**: the runtime actually exercises the live path rather than falling back to a stub or partial path

In shorthand:

`all-real = import-real ∧ path-real ∧ behavior-real across required layers`

This is a computed runtime state, not a label granted by configuration alone.

## Required components

Required layers for the all-real profile:
- **L1** EthicsCouncil
- **L2** TrustworthyAgentStack
- **L3** meaning-assay
- **L4** SOPHRON-CER / CER telemetry closure
- **Bridge** AttestAgentConlang seam availability

## Disposition constraints

- `PROCEED` may be synthesized only if required layers are behavior-real and `guard_runtime_disposition(...)` passes.
- Import success alone is never sufficient for `all-real`.
- Path presence alone is never sufficient for `all-real`.
- If any required layer degrades, that degradation must surface explicitly in adapter status, reports, or decision artifacts.

## detected_mode()

TrustedRuntime computes integration mode from observed runtime facts.

Modes:
- `stub`: no meaningful real surfaces detected
- `partial`: one or more layers have real import/path/behavior signals, but the full required set is not behavior-real
- `all-real`: all required layers are behavior-real

A requested mode via environment or CLI may be recorded, but it does not override the computed detected mode.

## Provenance expectations

Each adapter truth surface should distinguish:
- `import_real`
- `path_real`
- `behavior_real`

Maturity labels should derive from those facts, not replace them.

For the Attest/CER seam specifically, human-visible reports should preserve the typed CER verifier provenance block when available, including:
- `evaluated_at`
- `profile_hash`
- `known_message_set_hash`
- `signature_verifier_identity`
- `verifier_hash`
- `resolver_config_hash`

These fields document which verifier/config surface actually ran and was serialized into the decision artifact. They are provenance evidence, not a substitute for a green semantic verifier result or a broader security certification claim.

## Phase 1 scope

Phase 1 establishes:
- computed integration-mode detection
- explicit required-path expectations
- health/status surfacing for import/path/behavior truth
- test coverage for fallback truthfulness

Phase 1 does **not** by itself certify full L2 or L4 closure.

- Proposer-supplied resolver evidence (grants, status overrides, known refs arriving via action context) is tainted: it denies a clean `PASS`, downgrading to `REVIEW` with named `RESOLVER_INPUTS_PROPOSER_SUPPLIED` flags. All-real status never launders this taint; behavior-real layers with self-certified authority inputs still surface the flags in decision artifacts.
