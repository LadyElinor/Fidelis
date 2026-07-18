# Integration backlog

This backlog begins after the eight source histories are imported unchanged.

## P0: Preserve truth before refactoring

- Run and record every existing component test suite from its package root.
- Record exact imported commits in `provenance/imported-sources.tsv`.
- Capture current CLI outputs for TrustedRuntime's golden scenario and benchmark.
- Capture TrustworthyAgentStack's integration validation output.
- Do not change result language until baseline receipts are stored.

## P0: Resolve evidence-spine overlap

The current source cluster contains structural overlap that must be made explicit rather than hidden by the monorepo:

- CER-Telemetry currently references SOPHRON-CER as a Git submodule.
- SOPHRON-CER currently presents itself as an improved CER-Telemetry pipeline and contains collection, analysis, validation, and reporting concerns.
- TrustworthyAgentStack contains a runnable miniature path from EthicsCouncil through gating, CER export, and SOPHRON-style validation.

Required decisions:

1. Define CER-Telemetry as the event/telemetry producer and analysis package.
2. Define SOPHRON-CER as the independent receipt/invariant validator, or explicitly rename it if its actual scope remains broader.
3. Remove the nested SOPHRON submodule after both histories exist at top-level package paths.
4. Retain TrustworthyAgentStack's combined implementation as a reference fixture until production adapters replace it.
5. Add mutation tests proving SOPHRON catches altered CER records.

## P1: Package normalization

### EthicsCouncil

- Add a proper `pyproject.toml` and `src/ethics_council/` namespace.
- Preserve compatibility shims for `efm_council.py` and existing CLI usage.
- Export one typed `run_council` API.

### TrustworthyAgentStack

- Identify the authoritative Python package beneath the current mixed layout.
- Separate reference examples from reusable enforcement contracts.
- Keep the minimal full-stack proof as an integration fixture.

### AttestAgentConlang

- Package the reference implementation separately from specification documents.
- Mark cryptographic and resolver interfaces as delegated until fixed interoperability vectors exist.
- Expose canonicalization and verification through a narrow API.

### CER-Telemetry and SOPHRON-CER

- Standardize Node workspace metadata.
- Remove committed temporary-script naming from canonical entrypoints.
- Separate collectors, analyzers, receipt producers, and validators.

## P1: Runtime path normalization

- Remove neighboring-repository search assumptions from TrustedRuntime.
- Resolve adapters through installed workspace packages or explicit commands.
- Add a health record containing component version, commit, adapter mode, and test status.
- Ensure importability never implies independent corroboration.

## P1: Contract extraction

Extract only neutral duplicates:

- decision and execution identifiers;
- source identity and commit metadata;
- receipt references;
- adapter provenance states;
- serialization version identifiers;
- BELARION result envelope.

Do not extract:

- ethics scoring;
- warrant interpretation;
- runtime policy thresholds;
- telemetry analysis;
- final disposition logic.

## P2: BELARION advisory implementation

### meaning-assay

- Add native claim-level extraction.
- Add explicit promotion records.
- Add projection, constraint, exposure, and return assays.
- Emit `BelarionAssay` using `fidelis-contracts`.

### TrustedRuntime

- Accept native, derived-advisory, unavailable, and stub states.
- Render a separate BELARION report section.
- Make no disposition changes in the first release.

### CER/SOPHRON

- Store pre-outcome candidate and gate receipts.
- Add later outcome linkage without rewriting the original record.

## P2: Cross-layer integration tests

- Council unavailable: no autonomous proceed when profile requires it.
- meaning-assay unavailable: BELARION shown as unavailable, not silently derived.
- Attest envelope valid but source receipt altered: validation must fail.
- CER record changed after emission: SOPHRON must detect it.
- Same-lineage assessors agree: report agreement without claiming independence.
- High-significance, low-warrant private symbol: permit private reversible use.
- Unsupported identity projection affecting another person: block or require reformulation.

## P3: All-real release

- Clean-clone setup documented and automated.
- Exact Python and Node locks committed.
- All component tests pass from root CI.
- All-real profile rejects fallback and unpinned source states.
- Old repositories receive relocation notices and become read-only only after the tagged release.
