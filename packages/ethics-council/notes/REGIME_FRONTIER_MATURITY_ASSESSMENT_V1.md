# RegimeFrontierLab maturity and provenance assessment v1

Assessment date: 2026-05-13
Status: early but credible research scaffold
Purpose: judge whether `RegimeFrontierLab` is mature enough to support `EthicsCouncil` integration work

## Executive judgment

`RegimeFrontierLab` is mature enough to matter as an **offline calibration lab**.

It is **not** mature enough to function as a direct runtime authority layer for `EthicsCouncil`.

Best current classification:
- research seriousness: moderate
- reproducibility posture: promising
- metric maturity: early
- integration readiness for offline calibration: yes
- integration readiness for runtime bridge: no

---

## Verified artifact inventory

### Scripts present
- `scripts/run_followup_gfs_frontier_push_v1.py`
- `scripts/run_followup_gfs_patch_ab_v1.py`
- `scripts/run_targeted_followup_gfs_e1_e2_v1.py`

### Results present
- `results/e1/frontier_pareto.csv`
- `results/e1/plan_comparison.csv`
- `results/e1/summary.csv`
- `results/e2/delta_A2_minus_A0_ci.csv`
- `results/e2/summary_with_ci.csv`

This is enough to establish that the project contains real experiment scaffolding and persisted outputs, not just a manifesto.

---

## What looks solid enough

### 1. Experiment framing discipline
The project repeatedly marks itself as:
- model-bounded
- representation-dependent
- anti-universalist
- regime-conditioned

This is a strength. It reduces the risk of reading toy-simulator outputs as general truth claims.

### 2. Recognizable lab workflow
The scripts show real experimental structure:
- policy sweeps
- fixed seed lists
- summary aggregation
- Pareto / nondominance checks
- safety-envelope comparisons
- receipts/manifests
- compact Markdown reporting

This indicates a real research workflow rather than informal tinkering.

### 3. Directional result persistence
The results include:
- E1 comparative plan outputs
- E2 confidence-interval summaries
- summary CSVs that can be inspected externally

This makes the repo usable as a calibration annex, because outputs are already partially externalized.

---

## What is still immature

### 1. Small sample sizes
Observed replication counts are low:
- many E1 conditions use `n=4`
- E2 CI summary uses `n=8`

This is enough for directional signals, not strong inferential confidence.

### 2. Proxy-heavy measurement stack
Core metrics remain proxy-like:
- risk mass fraction
- semantic risk mass fraction
- utility proxy
- flourishing persistence
- coop score density
- motif-length survival
- hypervolume proxy

These may be useful, but they remain homemade abstractions. They should be treated as calibration instrumentation, not settled explanatory variables.

### 3. Substrate narrowness
The currently visible regimes are effectively concentrated around:
- narrative/library-like substrate
- GFS-like reflective/prosocial substrate
- patched variants of the above

This is not yet broad enough to stand in confidently for the regime diversity `EthicsCouncil` cares about.

### 4. Risk degeneracy in some outputs
Many result rows show `risk_mean = 0.0`.

That makes the frontier structure more about utility/flourish tradeoffs than about rich safety-pressure tradeoffs. It does not invalidate the lab, but it limits the force of safety claims.

### 5. No validated semantics bridge to EthicsCouncil
Nothing inspected so far establishes a tested mapping from:
- `EthicsCouncil` domains/lenses
n to:
- simulator controller families / regime-specific knobs

That bridge remains a design problem, not an achieved result.

---

## Script-level observations

### `run_targeted_followup_gfs_e1_e2_v1.py`
Strengths:
- computes summaries from persisted JSON outputs
- uses explicit dominance logic and hypervolume-point comparisons
- writes receipts and compact reports
- separates E1 policy-bank comparison from E2 ablation framing

Limitations:
- metrics are still built from internal proxies
- depends on pre-existing run directories and naming conventions
- regime comparison remains narrow and curated

### `run_followup_gfs_frontier_push_v1.py`
Strengths:
- defines explicit policy families
- uses multiple seeds
- computes summary, Pareto points, safety envelope, and report

Limitations:
- still narrow in corpus and parameter diversity
- utility proxy is hand-constructed from `lcc_fraction` and `stable_nontrivial_mass_fraction`

### `run_followup_gfs_patch_ab_v1.py`
Strengths:
- useful for provenance because it shows how patched corpora are constructed and compared
- includes an interpretable A/B structure and safety-envelope logic

Limitations:
- representation interventions are still bespoke and locally authored
- transferability beyond the immediate corpora is unknown

---

## Result-level observations

### E1
`plan_comparison.csv` shows a large directional improvement for regime-conditioned selection over a global anchor in aggregate hypervolume-point mean and flourish mean.

Interpretation:
- meaningful directional support for regime-conditioned policy-bank thinking
- not sufficient, by itself, to justify live deployment coupling

### E2
`summary_with_ci.csv` and `delta_A2_minus_A0_ci.csv` show:
- directionally positive shift in flourish and coop-density on patched representation
- some intervals still wide enough that confidence remains limited

Interpretation:
- representation patching likely matters
- but the effect size confidence is not yet strong enough for heavy downstream commitments

---

## Integration implications for EthicsCouncil

### Supported now
- offline calibration use
- controller-archetype comparison studies
- regime fragility analysis
- documentation and benchmark-case refinement informed by simulator evidence

### Not supported yet
- runtime augmentation of Council records
- automatic score or weight injection
- simulator-derived verdict language in end-user reports
- treating frontier outputs as direct moral recommendations

---

## Recommended next maturity checks

1. inspect `receipts.json` and any underlying run directories when available
2. expand seed counts for at least one narrow study before strong claims
3. test one mixed benchmark pack aligned to real EthicsCouncil domains
4. separate representation-limited failures from controller-limited failures explicitly
5. keep all bridge work offline until case-level downstream benefit is demonstrated

---

## Bottom line

`RegimeFrontierLab` is not vapor. It has enough real scaffolding and output discipline to be worth serious use as a research annex.

But its current maturity supports **calibration**, not **authority**.
