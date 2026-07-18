# Migration plan

## Decision

Create `LadyElinor/Fidelis` as the destination repository. Import all eight supplied repositories beneath `packages/` with full history using `git subtree` without squashing. AConstellation is now a source component, not the destination.

## Why subtree

- normal Git clone for users;
- component history remains available;
- no submodule initialization failure mode;
- atomic cross-component commits are possible;
- upstream repositories can remain available during transition;
- later subtree pulls remain possible while compatibility work continues.

## Procedure

1. Create and clone the new Fidelis repository.
2. Apply the monorepo seed.
3. Commit the seed before importing sources.
4. Run `./scripts/sync_components.sh import`.
5. Run `python scripts/verify_sources.py`.
6. Run each component's original test suite before modifying imports.
7. Establish a baseline report under `reports/baseline/`.
8. Replace neighboring-repository path discovery with monorepo-relative adapters.
9. Introduce shared contracts additively.
10. Add integration tests before moving any substantive logic.
11. Keep old repositories writable until the all-real profile is reproducible.
12. Archive old repositories only after a tagged monorepo release and migration notice.

## Migration waves

### Wave 1 — Physical import

No internal code moves. Preserve source layouts and make tests runnable from their package roots. Import AConstellation under `packages/aconstellation` and record any overlap with TrustedRuntime before moving or deleting logic.

### Wave 2 — Reproducible workspace

Add root test runner, source revision manifest, polyglot dependency installation, and truthful component health reporting.

### Wave 3 — Contract extraction

Move only duplicated neutral types into `fidelis-contracts`. Avoid a broad common-utilities package.

### Wave 4 — Adapter normalization

Replace arbitrary local-source search paths with explicit workspace-relative imports and commands.

### Wave 5 — BELARION advisory integration

meaning-assay emits a native BELARION result; TrustedRuntime displays it without enforcement; benchmark false positives and under-gating.

### Wave 6 — Narrow policy enforcement

Promote only calibrated BELARION tripwires to blocking status.

### Wave 7 — Release and archive

Publish a pinned all-real profile, tag the monorepo, and archive superseded repositories with relocation notices.

## Rollback

The original repositories remain the source rollback points until the first stable monorepo release. Every subtree import records the imported commit in `provenance/imported-sources.tsv`.
