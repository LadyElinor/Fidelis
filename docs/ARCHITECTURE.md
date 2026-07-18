# Architecture

## Governing principle

Fidelis is a modular monolith for development, testing, and release. It is not a monolithic authority.

The root repository owns:

- workspace tooling;
- cross-component contracts;
- integration tests;
- reproducible profiles;
- source provenance;
- architecture-boundary enforcement.

It does not own substantive ethical, warrant, enforcement, or telemetry judgments.

## Layer map

1. **Deliberation** — EthicsCouncil produces prospective hazards, convergences, fault lines, suspension triggers, and unresolved questions.
2. **Enforcement** — TrustworthyAgentStack turns declared policy and upstream findings into operational gates.
3. **Warrant sidecar** — meaning-assay distinguishes significance from warrant and owns BELARION qualification.
4. **Evidence spine** — CER-Telemetry records and analyzes execution evidence; SOPHRON-CER validates receipts and invariants.
5. **Integration** — TrustedRuntime orchestrates, canonicalizes, reports provenance, and synthesizes the operator-facing disposition.
6. **Message seam** — AttestAgentConlang wraps inter-layer claims without itself certifying their truth.
7. **Legacy integration source** — AConstellation is imported intact for comparison and reconciliation. It is not treated as an additional final authority; overlapping orchestration must be resolved explicitly.

## Dependency rule

Dependencies flow toward orchestration, never backward from an assessor into runtime policy.

```text
fidelis-contracts
      ↑
      ├── aconstellation
      ├── meaning-assay
      ├── ethics-council
      ├── trustworthy-agent-stack
      ├── attest-agent-conlang
      ├── cer-telemetry
      └── sophron-cer
                ↑
          trusted-runtime
```

Some operational edges, such as enforcement consuming EthicsCouncil output or SOPHRON validating CER output, are explicitly allowed in `contracts/dependency-policy.json`.

## Independence is not repository count

Independent repositories do not guarantee independent reasoning. In this monorepo, independence is instead protected by:

- one-way package dependencies;
- separately callable component APIs;
- separate test commands;
- separate receipts;
- explicit adapter provenance;
- assessor-lineage reporting;
- mutation tests that corrupt one layer and require another to detect it;
- no automatic upgrade from agreement to corroboration.

## Shared contracts

`packages/fidelis-contracts` contains only neutral types needed for serialization and cross-layer identity. It must not contain scoring rules, moral verdicts, policy thresholds, or telemetry analysis.

## Release profiles

The intended profiles are:

- `minimal`: contracts and deterministic local examples;
- `partial`: some real components, explicit stubs elsewhere;
- `all-real`: all required component implementations present and tested at pinned source revisions.

A profile must never call itself `all-real` merely because imports succeed. It must record source revisions, test results, adapter provenance, and required evidence surfaces.
