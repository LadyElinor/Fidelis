# All-Real Integration Profile

## Purpose

This document defines the reproducible "all-real" profile for TrustedRuntime.

"All-real" means the runtime executes against locally available, importable sibling integrations rather than falling back to stubbed or partial paths.

It does **not** imply independent corroboration. Real adapter execution and independence are separate axes.

## Required sibling integrations

TrustedRuntime expects these local integrations for full-path execution:

- `EthicsCouncil`
- `meaning-assay`
- `TrustworthyAgentStack`
- `SOPHRON-CER`

## Path resolution

TrustedRuntime resolves integrations through these environment variables first, then workspace-relative fallbacks:

- `ETHICS_COUNCIL_SRC`
- `MEANING_ASSAY_SRC`
- `TRUSTWORTHY_AGENT_STACK_SRC`
- `SOPHRON_CER_SRC`
- optional workspace override: `TRUSTED_RUNTIME_WORKSPACE_ROOT`

## Recommended workspace layout

```text
<workspace>/
  TrustedRuntime/
  EthicsCouncil/
  27assay/meaning-assay/src/
  repos/TrustworthyAgentStack-clean/
  repos/SOPHRON-CER-clean/
```

## Mode definitions

### stub mode

Only TrustedRuntime itself is installed. External siblings are absent.

Expected behavior:
- tests that require sibling integrations should skip explicitly
- adapter provenance may surface `STUB` or `UNAVAILABLE`
- benchmark outputs should report that real integration was not exercised

### partial mode

Some siblings are available, but not the whole stack.

Expected behavior:
- status surfaces mixed maturity such as `real`, `partially_wired`, `realish`, `stubbed`
- runtime may produce `PARTIAL` warrant provenance for unbacked translated families
- benchmark and reporting surfaces should show which integrations were actually exercised

### all-real mode

All sibling integrations above are locally available and importable.

Expected behavior:
- L1 hazard path runs real
- L2 TAS enforcement path runs real
- L3 meaning-assay warrant path runs real for backed families
- L4 telemetry/validation path runs at the currently supported real/realish surface
- integration-bound tests run instead of skipping

## Bootstrap checklist

1. Clone or mount all sibling repos.
2. Confirm each expected path exists.
3. Run:

```bash
trusted-runtime health
```

4. Confirm status output reflects the intended mode.
5. Run the full test suite.
6. If benchmarking external corpora, record whether benchmark results came from stub, partial, or all-real mode.

## Reporting rule

When publishing results, always report:

- integration mode: `stub`, `partial`, or `all-real`
- which sibling repos were actually available
- whether any tests were skipped because integration dependencies were missing
- adapter provenance separately from independence/correlation findings
