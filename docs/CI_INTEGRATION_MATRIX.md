# CI Integration Matrix

TrustedRuntime should be tested in three distinct profiles.

## 1. Stub profile

Purpose:
- prove the package installs and basic runtime surfaces work in isolation

Expected characteristics:
- sibling integrations absent
- dependency-bound integration tests skip explicitly
- no claim that all-real integration was exercised

## 2. Partial profile

Purpose:
- prove the runtime behaves honestly when some but not all sibling integrations are available

Expected characteristics:
- mixed adapter maturity surfaces
- `PARTIAL` and `realish` states may appear
- benchmark and report outputs must make exercised integrations visible

## 3. All-real profile

Purpose:
- prove the runtime can execute against the full locally wired stack

Expected characteristics:
- sibling integrations mounted and importable
- dependency-bound tests execute rather than skip
- benchmark outputs should record that all-real mode was exercised

## Reporting requirements

CI summaries should include:

- profile name
- passed count
- failed count
- skipped count
- dependency-bound tests skipped because integrations were unavailable
- adapter status snapshot from `trusted-runtime health`
- when decision reports are emitted, the CER verifier provenance block should be preserved so reviewers can see which Attest verifier/config surface actually flowed into the CER-facing artifact

## Minimal desired workflow split

- `ci-stub`
- `ci-partial`
- `ci-all-real`

Even before all workflows are automated, docs and local scripts should preserve this distinction so green results are not overread.
