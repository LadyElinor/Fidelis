# Fidelis

**A modular monorepo for governed agent reasoning, enforcement, evidence, and epistemic assay.**

Fidelis consolidates the LadyElinor governed-agent cluster into one reproducible workspace while preserving the independence of its authorities. The repository is physically unified; ethics, warrant, enforcement, communication, telemetry, and validation remain separate packages with explicit contracts and receipts.

## Why the name

**Fidelis** names the system's governing obligation: remain faithful to declared boundaries, evidence, provenance, and the people affected by a decision. The monorepo unifies development and release without allowing any component to become its own unquestioned authority.

## Component map

| Component | Monorepo path | Authority |
|---|---|---|
| TrustedRuntime | `packages/trusted-runtime` | orchestration, policy synthesis, operator reports |
| AConstellation | `packages/aconstellation` | legacy integration architecture retained for migration and reconciliation |
| EthicsCouncil | `packages/ethics-council` | prospective multi-lens hazard review |
| TrustworthyAgentStack | `packages/trustworthy-agent-stack` | execution gating and runtime enforcement |
| meaning-assay | `packages/meaning-assay` | significance, warrant, and BELARION qualification |
| AttestAgentConlang | `packages/attest-agent-conlang` | typed inter-agent messages and verification seams |
| CER-Telemetry | `packages/cer-telemetry` | telemetry collection and analysis |
| SOPHRON-CER | `packages/sophron-cer` | receipt validation and evidence-spine checks |
| Fidelis Contracts | `packages/fidelis-contracts` | shared neutral types only; no substantive judgments |

## Non-negotiable boundary

No component may silently certify itself.

- Ethical findings do not directly execute actions.
- Enforcement does not invent ethical or warrant standards.
- Meaning and warrant logic remain outside the orchestrator.
- Attest envelopes do not upgrade provenance by themselves.
- Receipts prove what was emitted, not that the emitting judgment was correct.
- TrustedRuntime synthesizes; it does not absorb the other authorities.

## Bootstrap

Apply this seed to a clean clone of `LadyElinor/Fidelis`, commit it, then import all eight source histories:

```bash
./scripts/sync_components.sh import
```

The import uses `git subtree` without `--squash`, preserving source history under each package prefix. To pull later upstream changes:

```bash
./scripts/sync_components.sh pull
```

Validate the workspace:

```bash
python scripts/verify_sources.py
python scripts/verify_boundaries.py
python scripts/run_component_tests.py
```

Or run the standard local checks:

```bash
make check
```

## BELARION

BELARION is integrated first as a neutral contract and advisory profile. Substantive qualification logic belongs in `meaning-assay`; policy consumption belongs in `TrustedRuntime`; durable candidate, gate, dissent, and outcome receipts belong in CER/SOPHRON.

See:

- `docs/BELARION_INTEGRATION.md`
- `docs/ARCHITECTURE.md`
- `docs/MIGRATION.md`
- `contracts/dependency-policy.json`

## Current seed status

This seed establishes the monorepo architecture, import/update automation, shared BELARION contracts, provenance manifest, dependency-policy declaration checks, CI, and integration tests. Component source code is populated by the subtree import script so that the authoritative Git histories remain intact.
