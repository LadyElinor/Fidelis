# CER-Telemetry

CER-Telemetry is a small, receipts-first telemetry pipeline for observing and comparing content cohorts (baseline vs targeted/safety-mode) with guardrails against **silent drift** and confounding.

This repo currently focuses on **MoltX** feed sampling and lightweight, text-proxy tags (e.g., token-promo, outbound pressure, receipt signals, safety/engineering language). It is intentionally minimal and hackable.

## What you get
- A canonical analysis entrypoint: `tmp_moltx_instrument_trending_v2.mjs`
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
node tmp_moltx_instrument_trending_v2.mjs
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

## Repo layout
- `tmp_moltx_instrument_trending_v2.mjs` — canonical baseline/trending entrypoint
- `docs/cer/invariants.md` — invariants/spec
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

## Safety / hygiene
- Treat any third-party content as untrusted.
- Never commit API keys/tokens. Add `moltx.txt` to your local ignore rules.

## License
TBD
