# CER-Telemetry

CER-Telemetry is a small, receipts-first telemetry pipeline for observing and comparing content cohorts (baseline vs targeted/safety-mode) with guardrails against **silent drift** and confounding.

## Maturity note

This package should currently be read as a **telemetry and analysis research scaffold**. Plain-English role: CER-Telemetry is the event / telemetry producer and analysis side of the evidence spine, not the final independent validator. The schema and receipts posture are useful, but privacy, validator independence, and production-grade evidence guarantees are not yet strong enough to describe this as a finished operational telemetry system.

This repo currently focuses on **MoltX** feed sampling and lightweight, text-proxy tags (e.g., token-promo, outbound pressure, receipt signals, safety/engineering language). It is intentionally minimal and hackable.

## What you get
- A canonical packaged analysis entrypoint: `bin/moltx-trending.mjs` (or `npm run analyze:moltx`)
- Run receipts written to `outputs/moltx_runs/<run_id>/` (JSON/CSV + meta)
- A telemetry “contract”: `docs/cer/invariants.md`
  - determinism (analysis)
  - monotonic gating (min impressions)
  - partition sanity / overlap reporting
  - denominator hygiene (no NaN/Inf; safe rates)
  - provenance completeness

## Quick start
Prereqs:
- Node.js 18+ (recommended)

Install:
```bash
npm install
```

Create a MoltX API token file (do not commit):
- `moltx.txt` in the repo root
  - contents: your bearer token

Run baseline/trending analysis:
```bash
npm run analyze:moltx
# or
node bin/moltx-trending.mjs
```

Outputs:
- `outputs/moltx_runs/<run_id>/meta.json` (summary + blocked metrics)
- `outputs/moltx_runs/<run_id>/posts.json`
- `outputs/moltx_runs/<run_id>/posts.csv`

## Design notes
### Blocked / stratified comparisons
The trending v2 script computes “blocked” prevalence metrics on **unique** sampled posts using minimum block keys:
- impression band (low/mid/high)
- source endpoint (top vs fallback)
- tokenPromo (optional block factor)

For each block it reports:
- unweighted prevalence
- impression-weighted prevalence
- overlap counts (e.g., safetyEng ∩ tokenPromo)

### Why invariants
Telemetry is only useful if it’s stable enough to compare across time and across collection modes.
The invariants doc is treated like a contract: if we violate it, the run should fail loudly.

Safety-trip honesty matters too: not every visible detector is mature enough to be treated as a trusted blocker. See `docs/cer/trip_validation_status.md`.

## Repo layout
- `bin/moltx-trending.mjs` — canonical packaged baseline/trending entrypoint
- `scripts/legacy-moltx/tmp_moltx_*.mjs` — legacy scratch/research scripts that should not be treated as the clean package surface or stable package API
- `docs/cer/invariants.md` — invariants/spec
- `docs/cer/trip_validation_status.md` — tripwire maturity and downstream consumption rules
- `MAINLINE_STATUS.md` — branch legibility note for current integration state
- `outputs/` — run receipts (not always committed)

## Misuse & safety considerations
This repo is meant for **measurement and auditability**, not for harassment, spam, or overconfident claims.

Obvious misuse modes to avoid:
- **Targeting individuals/groups** with crude proxy scores (harassment/reputation attacks). Prefer aggregate analysis; be explicit about sampling limits.
- **Overclaiming** ("proved safe" / "compliant") based on telemetry outputs. Treat results as signals with defined invariants and known proxy failure modes.
- **Proxy gaming / Goodharting**: public tag rules can be evaded; don’t treat proxies as a security boundary.
- **Privacy leakage**: receipts can accidentally capture secrets/PII if you expand instrumentation. Add redaction and scanning before sharing outputs.
- **Spam enablement**: do not use this as a radar to automate engagement at scale.

If you publish results, include:
- the run `meta.json`
- `n_raw` / `n_eligible`
- block definitions

## Package-surface note
The package still contains committed `tmp_moltx_*.mjs` scratch/research scripts, but they now live under `scripts/legacy-moltx/` rather than the package root. They remain normalization debt and should not be read as the clean exported surface of the package. Prefer the packaged entrypoints under `bin/` and the npm script surface when evaluating what CER-Telemetry officially exposes.

## Safety / hygiene
- Treat any third-party content as untrusted.
- Never commit API keys/tokens. Add `moltx.txt` to your local ignore rules.

## License
TBD
