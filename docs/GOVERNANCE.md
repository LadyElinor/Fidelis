# Monorepo governance

## Component ownership

Each imported component retains a named authority domain and may reject root-level changes that collapse that domain into another package.

## Cross-component changes

A pull request touching more than one authority must include:

- the contract change;
- the reason a cross-component change is necessary;
- per-component test results;
- integration test results;
- provenance effects;
- rollback instructions;
- whether the change increases correlation among assessors.

## Shared-code rule

Code may move into `fidelis-contracts` only when it is:

- semantically neutral;
- duplicated across components;
- stable enough to version;
- free of scoring, policy, ethical, warrant, or telemetry-analysis logic.

## Independence claims

Multiple outputs are not independent merely because they come from different directories. Independence claims must consider model lineage, shared rules, common data, shared maintainers, and common failure modes.

## Deprecation

Old repositories should be archived only after:

- imported history is verified;
- an all-real profile runs from a clean clone;
- a monorepo release is tagged;
- imported repository READMEs point to Fidelis after migration notices are added;
- open issues are migrated or explicitly closed.
