# Fidelis completion plan (2026-07-24)

This plan translates the authorized completion rubric into a concrete execution order grounded in the current local branch state.

## Current verified state
- Local working branch: `reconciliation/provenance-closure`
- Local HEAD: `a894a3baa3812e7bfb9df3683e7cc4406f84a098`
- The local branch includes runner hardening beyond the older public `32813a4` snapshot.
- Current CI workflow still lacks:
  - an always-run per-component summary print step after component tests
  - an always-run Git diagnostics step
  - explicit action-version modernization beyond the currently pinned `checkout@v4`, `setup-python@v5`, `upload-artifact@v4`

## Completion standard
Fidelis is complete only when it can:
1. accept a real proposed action
2. run every required authority without hidden fallback certification
3. emit a validated evidence chain
4. fail closed on unsafe execution
5. reproduce the same result from a clean clone

## Execution order

### Tranche 1: expose exact CI failures
- Add always-run component summary printing after `scripts/run_component_tests.py`
- Add always-run Git diagnostics at the tail of CI jobs
- Verify uploaded artifact coverage for:
  - `reports/component-tests.json`
  - `reports/component-logs/*.stdout.log`
  - `reports/component-logs/*.stderr.log`
- Re-run or push and inspect the next red workflow honestly

### Tranche 2: fix the actual failing component rows
- Use surfaced component result rows and logs
- Fix the narrow failing component(s) or fixture(s)
- Keep minimal/all-real semantics intact

### Tranche 3: declarative component registry
- Introduce `contracts/component-registry.json`
- Move hard-coded setup/test orchestration toward registry-driven execution
- Keep transitional compatibility until all components are normalized

### Tranche 4: normalize authority package surfaces
- EthicsCouncil packaging/API/CLI
- TrustworthyAgentStack package boundary cleanup
- AttestAgentConlang narrow package/API surface
- TrustedRuntime adapter resolution away from neighboring-repo assumptions
- CER/SOPHRON role separation and mutation tests

### Tranche 5: canonical end-to-end evaluate command
- Add root evaluation CLI
- Preserve architectural rule that TrustedRuntime synthesizes but does not silently rewrite authority findings
- Emit governed transaction output with receipts and fail-closed flags

### Tranche 6: complete receipt chain and authorization receipt
- Strengthen component-test receipt fields
- Bind runtime-health to component-test digest
- Add final `authorize_release.py` receipt emission
- Preserve distinction between production correctness and side-effect permission

### Tranche 7: safe side-effect execution
- Add executor protocol
- Require valid authorization receipt, matching request/action digests, expiry, idempotency, and approval gates
- Emit execution outcome receipts and preserve dissent/override state

### Tranche 8: adversarial and mutation testing
- Cross-layer corruption, replay, stale-digest, timeout, override, duplicate, interruption, and compensation scenarios
- Verify both decision behavior and evidence-chain behavior

### Tranche 9: observability and continuous provenance enforcement
- Correlation IDs across request/decision/execution/receipts
- Structured JSON logs
- Runtime health/readiness/version/commit/adapter visibility
- Strong imported-prefix enforcement on PRs and protected-branch pushes

### Tranche 10: promotion and release
- Green seed-integrity and all-real-integration
- Confirm provenance/live-tree equality
- Preserve history on merge
- Re-run all checks on merged master
- Protect branch
- Run clean-clone / setup / check / all-real / demo / release-check gates before tagging 1.0

## Immediate focus
The current unblocker remains tranche 1: reveal the exact failing CI rows and preserve better Git-state diagnostics, without weakening profile semantics or misclassifying the cleanup error as the root cause.
