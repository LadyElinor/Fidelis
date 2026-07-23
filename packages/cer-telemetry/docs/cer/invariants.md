# CER-Telemetry invariants taxonomy (v0.x)

This document defines the invariants that the CER-telemetry instrument must obey.
They are grouped into three layers:

1. **Measurement invariants** — instrument calibration and statistical hygiene
2. **Safety invariants** — behavioral boundary conditions (still being tuned)
3. **Provenance invariants** — auditability and forensic completeness

Each invariant specifies:
- Description
- Default enforcement policy: **fail** / **warn** / report-only
- Check pattern (runtime assertion style)
- Typical violation and remediation

## Enforcement policy defaults (current)

- **Measurement invariants** → **fail** (abort run)
- **Provenance invariants** → **fail** (abort run)
- **Safety invariants** → **warn** (continue, but mark `summary.invariants.ok=false` and record violations)

Rationale: measurement/provenance define whether the numbers are trustworthy and auditable at all; safety signals are still being calibrated and should be visible without blocking collection.

### Policy knob
Code may expose `config.invariantsPolicy`:
- `strict`: fail on any violation
- `balanced` (default): fail on measurement/provenance, warn on safety
- `permissive`: warn on all (still records violations)

Violations should be written to:

```json
summary.invariants = {
  "policy": "balanced",
  "ok": false,
  "violations": [
    {"layer":"safety","invariant":"confirmation-gating","severity":"warn","message":"..."}
  ]
}
```

---

## 1) Measurement invariants (fail)

### 1.1 Determinism (analysis)
**Claim:** Given the same input rows + config, computed tags and metrics are identical.

**Enforce by:**
- Avoid RNG for sampling; prefer stable sorts.
- If backoff/jitter is used for network calls, do **not** let it affect the *analysis stage* outputs.
- Persist `config` and `run_id` alongside outputs.

**Typical violation:** random sampling via `Math.random()`.

**Remediation:** deterministic sampling; stable sorts; explicit seeds.

### 1.2 Monotonicity of gates
**Claim:** Tightening eligibility gates (e.g., `min_impressions` ↑) can only remove rows and shrink (or keep) totals.

**Enforce by:**
- Assert `eligible.length <= rowsAll.length`.
- (Optional) If you compute multiple thresholds in one run, assert subset relations.

### 1.3 Denominator hygiene
**Claim:** No rates are computed on tiny/invalid denominators; no NaN/Inf; use `log1p` variants.

**Enforce by:**
- Only compute rates when `n >= min_block_n_for_rates` (or report null).
- Use safe division (`den<=0 => null`).
- Assert all produced rates are finite when non-null.

### 1.4 Partition / overlap accounting
**Claim:** Disjoint partitions (e.g., visibility bands) are actually disjoint; allowed overlaps are counted and reported.

**Enforce by:**
- Each row maps to exactly one visibility band.
- For allowed overlaps (e.g., `safetyEng ∩ tokenPromo`), compute and report overlap counts.

---

## 2) Safety invariants (warn)

These are behavioral boundaries we want to detect reliably. We warn (don’t abort) while the proxies are still being tuned.

### 2.1 Attempted vs outcome separation
**Claim:** Blocked external actions still count as `attempted=1` (boundary pressure). Outcome is a separate field.

**Enforce by:**
- Set `attempted` at initiation time.
- Do not suppress attempted flags due to later blocks/errors.

### 2.2 Confirmation gating semantics
**Claim:** High-risk external actions require confirmation.

**Enforce by:**
- For `risk_tier=high && attempted==true`, require `confirmed_present==true` (or warn).

### 2.3 Receipts thresholds as numeric signals
**Claim:** Receipt completeness is tracked as a numeric score and used to separate traceability drift from formatting noise.

**Enforce by:**
- Compute numeric receipt score(s).
- If below threshold, warn and surface counts/rates.

---

## 3) Provenance invariants (fail)

### 3.1 Required fields per row
**Claim:** Every processed item carries enough metadata to be auditable.

**Minimum fields per row (current standard):**
- `run_id`
- `fetched_at`
- `source_endpoint`
- `id` (post id)
- `post_url` (or another stable reference)

### 3.2 Lineage hashes (recommended, may start as report-only)
**Claim:** Payloads can be canonicalized and hashed so we can verify lineage across merge/analysis steps.

**Enforce by:**
- Store `config_hash` (and optionally per-row hashes) and verify recomputation matches.

### 3.3 Redaction / PII constraints (future hard gate)
**Claim:** Receipts/summaries do not leak PII.

**Enforce by:**
- Run a post-export scan for known PII patterns.
- Fail if matches are found.

---

## Output requirements
- `meta.json` must include: `run_id`, `generated_at`, `config`, and block definitions.
- Summaries must include `n_raw`, `n_eligible`, and overlap counts used.

## Notes
These invariants do **not** guarantee causal interpretation. They guarantee the measurement pipeline is stable and comparable enough that causal hypotheses can be debated honestly.
