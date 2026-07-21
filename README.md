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

**Important:** seed/bootstrap checks are not production authorization.

Until the declared authorities are materially imported and the `all-real` profile verifies cleanly, treat this repository as:
- `PRODUCTION_CLEARED=false`
- `SIDE_EFFECTS_ALLOWED=false`
- `SUBSTANTIVE_ETHICS_TESTED=false`

Apply this seed to a clean clone of `LadyElinor/Fidelis`, commit it, then inspect the required materialization plan:

```bash
./scripts/sync_components.sh plan
```

For machine-readable bootstrap planning, emit JSON instead:

```bash
./scripts/sync_components.sh plan-json
```

To fail fast when the workspace is not yet materially complete for all-real bootstrap:

```bash
python scripts/check_bootstrap.py
# or
make bootstrap-check
```

For a compact machine-readable bootstrap summary:

```bash
python scripts/check_bootstrap.py --summary-json
```

Then import all eight source histories:

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

`verify_boundaries.py` currently validates:
- declared component dependency policy shape and acyclicity
- observed Python `src` imports against production policy
- observed Python `tests` imports against explicit test policy
- observed JS/TS `src` imports against production policy when local Node package roots exist
- observed JS/TS `tests` imports against explicit test policy when local Node test roots exist
- observed Node `package.json` dependency fields (`dependencies`, `devDependencies`, `peerDependencies`, `optionalDependencies`) against production policy when local Node packages exist

Or run the standard local checks:

```bash
make check
```

A green `make check` or minimal-profile run means seed/dev integrity only. It must not be described as all-real validation, ethical clearance, or authorization for consequential side effects.

## BELARION

BELARION is integrated first as a neutral contract and advisory profile. Substantive qualification logic belongs in `meaning-assay`; policy consumption belongs in `TrustedRuntime`; durable candidate, gate, dissent, and outcome receipts belong in CER/SOPHRON.

See:

- `docs/BELARION_INTEGRATION.md`
- `docs/ARCHITECTURE.md`
- `docs/MIGRATION.md`
- `contracts/dependency-policy.json`

## Current seed status

This seed establishes the monorepo architecture, import/update automation, import planning visibility, shared BELARION contracts, provenance manifest, dependency-policy declaration checks, observed-edge boundary enforcement, CI, and integration tests.

Current authorization posture:
- seed / minimal profile: development-safe, not production-cleared
- side effects: not authorized
- substantive ethics performance: not yet demonstrated in the seed alone
- all-real profile: required for materially complete runtime verification

Current boundary enforcement status:
- Python `src` imports are checked against declared production policy when local package roots are present.
- Python `tests` imports are checked against explicit `test_may_depend_on` policy when local test roots are present.
- JS/TS `src` imports are checked against declared production policy when local Node package roots are present.
- JS/TS `tests` imports are checked against explicit test policy when local Node test roots are present.
- Node `package.json` dependency fields are checked against declared production policy when local Node packages are present.

The seed remains careful about applicability. When a language/runtime surface is not physically present in the local workspace, the validator reports that the check was not applicable rather than overstating coverage. Component source code is still populated by the subtree import script so that the authoritative Git histories remain intact.
