# ADR-0001: Consolidate into Fidelis

- Status: accepted
- Date: 2026-07-17

## Context

The governed-agent stack is operationally coupled but physically distributed. Local-path imports, uneven release status, and coordinated schema changes make reproducibility harder than the repository separation makes independence stronger.

## Decision

Create Fidelis as a polyglot monorepo. Import all eight supplied component histories, including AConstellation, with unsquashed Git subtrees. Preserve independent package APIs, tests, receipts, and one-way dependencies.

## Consequences

Positive:

- atomic integration changes;
- one reproducible source revision set;
- simpler CI and onboarding;
- easier BELARION implementation;
- fewer misleading unavailable-adapter states.

Risks:

- accidental logic collapse;
- common-mode failures;
- root tooling becoming an authority;
- broad refactors obscuring component provenance.

Controls:

- dependency-policy checks;
- separate component test execution;
- independent receipts;
- source provenance manifest;
- explicit cross-component review rules.
