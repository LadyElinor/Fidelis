# Regime bridge offline design v1

Status: recommended prototype direction
Source seed: `Omnius/regimewrapper.txt`
Supersedes: any immediate runtime bridge proposal

## Design stance

This design keeps `RegimeFrontierLab` in an **offline calibration role**.

It explicitly does **not**:
- modify live `EthicsCouncil` verdicts at runtime,
- inject simulator scores into `run_council()` output,
- auto-tune weights from a single batch,
- present simulator outputs as direct moral recommendations.

The bridge should produce calibration artifacts for humans to inspect, then selectively feed back only narrow lessons into case design, lens phrasing, or synthesis constraints.

---

## Why the original wrapper is not safe as-is

The draft wrapper in `Omnius/regimewrapper.txt` is useful as a concept sketch but unsafe to adopt directly because:

1. it assumes simulator fields that do not appear to be returned directly by `sim_memetic_gelation.run()`
2. it invents live runtime semantics for `risk_bias` / `flourish_bias` before validation
3. it maps some non-domain concepts as if they were `detect_domains()` keys
4. it assumes a repo layout different from the currently verified local source path
5. it turns a calibration lab into a post-processing authority layer too early

The right move is to preserve the wrapper's useful ideas while shifting them into an offline batch workflow.

---

## Safe bridge shape

### Proposed file
- `EthicsCouncil/regime_bridge_offline.py`

### Purpose
Given:
- a small benchmark pack of EthicsCouncil cases,
- a translation spec from domains/lens-clusters to regime/controller archetypes,
- a configured local `RegimeFrontierLab` source path,

produce:
- a calibration report,
- a per-case regime classification note,
- a per-archetype comparison table,
- a short interpretation layer describing regime fragility / robustness.

### Inputs
1. `EthicsCouncil` benchmark case list
2. `EthicsCouncil` translation spec
3. local `RegimeFrontierLab` path
4. selected controller archetypes
5. selected regimes
6. seed list

### Outputs
Write only research artifacts, for example:
- `EthicsCouncil/output/regime_bridge/<study_name>/case_regime_map.csv`
- `EthicsCouncil/output/regime_bridge/<study_name>/archetype_summary.csv`
- `EthicsCouncil/output/regime_bridge/<study_name>/transfer_summary.csv`
- `EthicsCouncil/output/regime_bridge/<study_name>/report.md`
- `EthicsCouncil/output/regime_bridge/<study_name>/receipts.json`

No output should be appended automatically to live Council records.

---

## Recommended runtime boundary

### What the wrapper may do
- read benchmark definitions
- read translation spec
- call `EthicsCouncil` locally to obtain domain tags / lens outputs for benchmark cases
- launch `RegimeFrontierLab` batch scripts or controlled direct simulator runs
- compute comparison summaries from emitted JSON/CSV artifacts
- write a human-readable calibration report

### What the wrapper should not do yet
- call `attach_regime_bridge(record, ...)` inside `run_council()`
- append `regime_bridge` fields to final user-facing report by default
- translate a wide/narrow frontier directly into `PERMIT`, `CAUTION`, `PROHIBIT`, or `SUSPEND`
- rewrite lens weights automatically

---

## Minimal architecture

### Step 1: classify benchmark cases
For each selected case:
- run `EthicsCouncil`
- capture:
  - detected domains
  - top fault lines
  - stability state
  - whether suspension triggered
- map to a rough regime class using the translation spec

This creates a case->regime planning table, not a verdict bridge.

### Step 2: choose controller archetypes
Do not map one lens to one simulator policy.
Use controller archetypes derived from lens clusters, such as:
- safety-first / contamination-averse
- legitimacy-preserving proceduralist
- care-extended vulnerability-sensitive
- truth-correction / reopening
- flourishing-bridge / cooperative persistence

### Step 3: run offline studies
For each regime x controller archetype combination:
- run a small seed set
- record:
  - risk proxy
  - semantic risk proxy
  - utility proxy
  - flourishing persistence
  - coop score density
  - motif-length survival
  - any frontier / nondominance summaries available from the batch study

### Step 4: interpret only at the calibration level
Interpretive outputs should say things like:
- "care-extended controller appears regime-fragile under safety-stress conditions"
- "legitimacy-preserving proceduralist remains safety-nonworse while widening the frontier in legitimacy-sensitive regimes"
- "abstract-social regimes appear more representation-limited than controller-limited"

They should not say:
- "therefore this live case is morally permitted"

---

## Safer adaptation of ideas from the draft wrapper

### Keep
- domain -> regime mapping concept
- compact summary artifact concept
- bridge as adjunct, not replacement
- possibility of human-readable interpretation text

### Discard for now
- direct runtime hook in `efm_council.py`
- heuristic `risk_bias` and `flourish_bias` derived from live lens verdicts
- assumed `final` fields like `frontier_width` / `hypervolume` / `safety_envelope_ok` unless verified in actual emitted outputs

### Replace with
- explicit study configs
- pre-registered seed lists
- summary files computed from actual script outputs
- interpretation tied to CSV evidence, not assumed return keys

---

## Suggested CLI shape

Example future command:

```bash
python regime_bridge_offline.py --study benchmark_pack_v1 --regime-lab-root "C:\Users\arren\Molt\workspace\RegimeFrontierLab"
```

Optional flags:
- `--case-pack notes/REGIME_BENCHMARK_PACK_V1.md`
- `--translation-spec notes/REGIME_TRANSLATION_SPEC_V1.md`
- `--seeds 4`
- `--dry-run`
- `--reuse-existing-results`

---

## Interpretation contract

Any report generated by the offline wrapper must include language like:
- model-bounded
- simulator-bounded
- representation-dependent
- calibration evidence only
- not a direct EthicsCouncil verdict input

This keeps the epistemic boundary visible.

---

## Immediate implementation recommendation

If implemented soon, build only **v0**:
- a batch runner that reads a fixed benchmark pack
- maps each case to a regime class
- points to pre-existing `RegimeFrontierLab` study outputs or launches a small study
- writes one report comparing controller archetypes per regime

Do not attempt live coupling in v0.

---

## Bottom line

The right descendant of `regimewrapper.txt` is not `regime_bridge.py` inside live Council flow.

It is an **offline calibration wrapper** that helps answer:
- which ethical stances appear regime-robust,
- which are regime-fragile,
- and where representation limits, not ethical stance, explain poor frontier behavior.
