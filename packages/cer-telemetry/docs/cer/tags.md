# CER Telemetry tag registry (v0.x)

This file defines the canonical CER-telemetry tags used in analysis.

For each tag we record:
- **Definition (human)**: what we mean
- **Detection (rule)**: how the pipeline currently detects it (proxy)
- **Common false positives / caveats**: where the proxy fails
- **Suggested refinements**: how we might improve it later

> Goal: keep tag semantics stable over time, and make changes explicit.

## Tag: tokenPromo
- **Definition:** Content primarily promoting tokens/airdrops/CA/price action.
- **Detection:** Regex proxy (see `tmp_moltx_instrument_trending_v2.mjs` `RX.tokenPromo`).
- **Common false positives:**
  - Security discussions that mention “token” or “0x…” in an analytical context.
  - Legit technical posts that include a contract address without promotional intent.
- **Suggested refinements:**
  - Add negative keywords (e.g., "scam", "warning", "avoid") to reduce safety posts being labeled promo.
  - Separate “address mentioned” from “promotion” into two tags.

## Tag: safetyEng
- **Definition:** Safety/engineering/telemetry/instrumentation discourse.
- **Detection:** Regex proxy (`RX.safetyEng`).
- **Common false positives:**
  - Posts that use “risk” colloquially.
  - Posts that mention “audit” unrelated to technical auditability.
- **Suggested refinements:**
  - Add a second stricter tag (e.g., `safetyEng_strict`) based on multiple hits.

## Tag: attempted_external_cta
- **Definition:** Boundary pressure / call-to-action that attempts to induce external side effects (DM, click, sign, verify, connect wallet, etc.).
- **Detection:** Regex proxy (`RX.cta`).
- **Common false positives:**
  - Benign CTAs ("join the discussion") if regex is too broad.
  - Quoted text from others.
- **Suggested refinements:**
  - Separate high-risk wallet CTAs from low-risk “follow/join”.

## Tag: attempted_external_link
- **Definition:** Contains an external link but without CTA pressure language.
- **Detection:** URL regex hit + NOT CTA.
- **Common false positives:**
  - “Link” that is just a domain mention.
- **Suggested refinements:**
  - Improve URL detection; split by domain class (github/basescan vs unknown).

## Tag: attempted_external_any
- **Definition:** Union of attempted external surfaces: `attempted_external_cta OR attempted_external_link`.
- **Detection:** Derived.
- **Caveat:** Not all links are risky; interpret by block and context.

## Tag: receipt_score (and derived thresholds)
- **Definition:** A checklist-style proxy for “receipts” / verifiability.
- **Detection:** `countChecklist()` counts the presence of signals:
  - repo link
  - commit/hash
  - transaction/explorer ref
  - ABI/interface mention
  - reproducible steps
- **Derived tags:**
  - `receipt_score_ge_2`
  - `receipt_score_ge_3`
- **Common false positives:**
  - Posts that mention these words without actual usable receipts.
- **Suggested refinements:**
  - Domain-aware checks (real github URLs, real commit hashes, real explorer links).

## Tag: hasUrl / hasCTA
- **Definition:** helper flags used to build other tags.
- **Detection:** regex.

## Policy on tag changes
- If detection rules change, bump a version in this file and note the diff.
- When possible, include a short "before/after" example.
