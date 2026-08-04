# Integration backlog

This backlog begins after the eight source histories are imported unchanged.

## P0: Preserve truth before refactoring

- Run and record every existing component test suite from its package root.
- Record exact imported commits in `provenance/imported-sources.tsv`.
- Capture current CLI outputs for TrustedRuntime's golden scenario and benchmark.
- Capture TrustworthyAgentStack's integration validation output.
- Do not change result language until baseline receipts are stored.

## P0: Resolve evidence-spine overlap

Current plain-English role split to preserve until deeper refactor:
- **CER-Telemetry** should be treated as the event / telemetry producer and analysis package.
- **SOPHRON-CER** should be treated as the independent receipt / invariant validator.
- If SOPHRON continues to contain broader pipeline behavior, that scope should either be reduced or renamed explicitly rather than left ambiguous.

The current source cluster contains structural overlap that must be made explicit rather than hidden by the monorepo:

- CER-Telemetry currently references SOPHRON-CER as a Git submodule.
- SOPHRON-CER still contains traces of older "improved CER-Telemetry" identity and currently mixes collection, analysis, validation, and reporting concerns.
- TrustworthyAgentStack contains a runnable miniature path from EthicsCouncil through gating, CER export, and SOPHRON-CER-style validation.

Required decisions:

1. Define CER-Telemetry as the event/telemetry producer and analysis package.
2. Define SOPHRON-CER as the independent receipt/invariant validator, or explicitly rename it if its actual scope remains broader.
3. Remove the nested SOPHRON submodule after both histories exist at top-level package paths.
4. Retain TrustworthyAgentStack's combined implementation as a reference fixture until production adapters replace it, and document plainly that the fixture demonstrates one bounded path rather than final authority collapse.
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

CER-Telemetry package-normalization checklist:
- Canonical packaged entrypoints should live under explicit package surfaces (`bin/`, exported modules, or clearly named npm scripts) rather than root-level `tmp_*` files.
- Root-level scratch or one-off research scripts should be moved, retired, or labeled as non-canonical normalization debt rather than described as the package API.
- Package docs should point users at packaged entrypoints first, even while legacy scratch surfaces still exist.
- Token-bearing or local-operator workflows (for example `moltx.txt` usage) should stay clearly documented as local/manual rather than silently implied as clean package behavior.

SOPHRON-CER package-normalization checklist:
- Canonical validator-facing commands should stay narrow and explicit (`validate`, `report`, and only other commands that clearly belong to validator scope).
- Research/example flows should remain visibly namespaced as examples rather than reading like first-class validator operations.
- Package metadata should not imply publish-ready scope while mixed research/validator surfaces still coexist.
- Dependencies should be justified by the currently exercised validator or example surface, not retained as ambient capability signals.
- Local lint/doc tooling should not be treated as a quality gate signal unless it is updated, exercised, and intentionally wired into CI.
- Legacy identity strings (for example older CER-Telemetry naming) should be removed except where retained deliberately as migration/explanation notes.

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
- If the mind-ontology diagnostic proceeds, start with neutral receipt/observation types and black-box probe support only, following `docs/MIND_ONTOLOGY_DIAGNOSTIC_PLAN.md`.

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

## Follow-on planning notes

After the provenance-closure promotion to `master`, several larger next-step documents now exist and should inform future backlog execution:

- `docs/COMPLETION_ROADMAP.md`
- `docs/SECURITY_NEXT_STEPS.md`
- `docs/SAFETY_PROPOSAL.md`
- `docs/MIND_ONTOLOGY_DIAGNOSTIC_PLAN.md`

The backlog remains the short-form execution tracker. Those design notes provide the larger sequencing and architectural rationale for the next development stages.
