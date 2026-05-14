# RegimeFrontierLab -> EthicsCouncil offline integration plan

Status: recommended
Scope: offline calibration and research workflow only
Not recommended yet: runtime coupling, live verdict augmentation, or automated weight updates from simulator output

## Why this plan exists

`EthicsCouncil` and `RegimeFrontierLab` are philosophically adjacent but operationally different.

- `EthicsCouncil` is a deterministic ethical diagnostics scaffold for case-wise hazard detection under uncertainty.
- `RegimeFrontierLab` is a model-bounded simulation toolkit for mapping safety-utility-flourishing tradeoff frontiers across different environment regimes.

The right first integration is **offline calibration**, not inline authority.

## Core principle

Use `RegimeFrontierLab` to test whether a policy family, lens family, or synthesis stance appears:
- regime-aligned or regime-misaligned,
- frontier-widening or frontier-collapsing,
- safety-nonworse or safety-regressive,

then feed those lessons back into `EthicsCouncil` as carefully scoped heuristics, wording refinements, calibration notes, or new benchmark cases.

Do **not** let simulator outputs directly determine end-user recommendations at this stage.

---

## Phase 1: establish a translation layer

### Goal
Create a minimal mapping from `EthicsCouncil` concepts to `RegimeFrontierLab` concepts without pretending they are identical.

### 1A. Map EthicsCouncil domains to rough regime classes

This should be a planning artifact first, not code.

Suggested initial mapping:

- `criminal_justice` -> safety-stress / legitimacy-sensitive regime
- `engineering_safety` -> catastrophic-risk / burden-of-proof regime
- `personhood` -> abstract-social / recognition-sensitive regime
- `identity` -> abstract-social / tragic-conflict regime
- `security` -> suspicion-escalation / legitimacy-sensitive regime
- `noninterference` -> doctrine-collision / extinction-stakes regime
- `medical` -> vulnerability-dense / throughput-pressure regime
- `sustainability` -> distributed-impact / long-horizon regime
- `finance`, `procurement`, `marketing`, `privacy` -> institutional-trust / disclosure / incentive-distortion regimes

### 1B. Map lens clusters to controller archetypes

Do not map each lens one-to-one yet. Start with clusters.

Suggested controller archetypes:

1. **safety-first / contamination-averse**
   - strongest analogs: `kantian`, `institutional`, `stoic`
   - style: halt, gate, verify, reduce contamination, preserve auditability

2. **legitimacy-preserving proceduralist**
   - strongest analogs: `institutional`, `confucian`, `contractualist`
   - style: preserve due process, role integrity, public trust, reversible review

3. **care-extended vulnerability-sensitive**
   - strongest analogs: `care_ethics`, `trustee`, `relational_ontology`
   - style: protect dependents, surface offloaded harms, widen attention to vulnerable parties

4. **truth-correction / reopening oriented**
   - strongest analogs: `stoic`, `institutional`, `genealogical`, parts of `confucian`
   - style: revisit closure, test corrective evidence, resist reputation-protective finality

5. **flourishing-bridge / cooperative persistence**
   - weaker current match inside `EthicsCouncil`
   - likely draws from `care_ethics`, `relational_ontology`, and selective `virtue`
   - note: this is where `RegimeFrontierLab` may reveal a gap in `EthicsCouncil`

### Deliverable
- one Markdown spec file defining these mappings
- no runtime code yet

---

## Phase 2: choose benchmark case packs for offline calibration

### Goal
Run not all cases, but a small handpicked pack where regime distinctions actually matter.

Recommended first benchmark pack:

1. **criminal justice hazard**
   - `CASE-011` coercive contamination
2. **criminal justice correction**
   - `CASE-012` voluntary corroborated reopening
3. **criminal justice protective benchmark**
   - `CASE-013` PEACE-style interviewing
4. **engineering safety**
   - one catastrophic-risk / burden-of-proof case
5. **identity/personhood**
   - one emergent-person or recognition-conflict case
6. **sustainability or privacy**
   - one diffuse-harm / institutional-trust case

### Why this mix
This pack tests:
- hazard vs correction vs protective procedure,
- catastrophic risk vs recognition conflict,
- acute procedural harm vs diffuse trust harm.

### Deliverable
- `notes/regime_benchmark_pack_v1.md`
- list cases, intended regime class, expected controller tensions, and what would count as a useful result

---

## Phase 3: define evaluation questions before running anything

### Goal
Avoid post hoc narrative drift.

Before using the simulator, pre-register questions like:

1. Does a given controller archetype appear to widen or collapse the frontier in a given regime?
2. Does a safety-first style transfer well from safety-stress regimes into abstract-social ones, or does it become degenerately restrictive?
3. Do flourishing-oriented controller settings retain safety envelope discipline in narrative-rich environments but fail in legitimacy-sensitive ones?
4. Does any controller family show stable non-dominated behavior across multiple regime classes, or is specialization consistently better?

### Deliverable
- `notes/regime_frontier_questions_v1.md`

---

## Phase 4: run offline experiments as calibration studies

### Goal
Use `RegimeFrontierLab` to compare controller archetypes by regime, not to score moral truth.

### Recommended study types

#### 4A. Archetype sweep by regime
For each regime class, test:
- safety-first
- legitimacy-preserving
- care-extended
- truth-correction
- flourishing-bridge

Observe:
- frontier width / hypervolume proxy
- safety envelope pass/fail
- utility retention where available
- whether controller specialization beats any one global controller

#### 4B. Transfer study
Train/tune on one regime class, then evaluate on another.
Examples:
- safety-stress -> abstract-social
- abstract-social -> safety-stress
- legitimacy-sensitive -> narrative-rich

Key question:
- which EthicsCouncil stances are robust versus regime-fragile?

#### 4C. Representation sensitivity study
Particularly for abstract-social or personhood-like material:
- test whether controller changes alone matter,
- or whether representation/corpus patching dominates outcomes.

This matters because a bad result may reflect the simulator substrate, not a bad ethical stance.

### Deliverable
- results tables stored in `EthicsCouncil/notes/` or a dedicated cross-repo notes folder
- each run interpreted as calibration evidence, not verdict evidence

---

## Phase 5: feed back only narrow, survivable lessons

### Goal
Translate simulator findings into modest EthicsCouncil improvements.

Allowed feedback types:

1. **lens wording refinement**
   - e.g. some controller archetype repeatedly collapses a regime because it erases subordinated duties or over-compresses uncertainty

2. **synthesis caution rules**
   - e.g. if a regime class is consistently frontier-narrow, require more suspension or contested outputs

3. **new benchmark cases**
   - use simulator insight to design stronger human-readable calibration cases

4. **documentation updates**
   - document where certain ethical stances appear regime-fragile

Not yet allowed:
- automatic runtime score injection
- automatic lens-weight rewriting
- replacing case reasoning with simulator recommendations

---

## Phase 6: possible future bridge, only after evidence

A runtime or semi-runtime bridge is only worth considering if all of the following become true:

1. regime classification is stable enough to be meaningful
2. controller archetypes are interpretable and not arbitrary
3. frontier outputs are reproducible enough to survive seed variation
4. simulator findings consistently improve downstream case calibration
5. documentation clearly preserves the distinction between:
   - heuristic case diagnosis
   - simulated frontier exploration

If those conditions are met, the first bridge should be **advisory only**, for example:
- append a lab note such as:
  - "offline frontier studies suggest this policy family is regime-fragile under safety-stress conditions"
- never convert that into a direct recommendation without human-readable explanation

---

## Immediate next actions

### Recommended next action 1
Create a small planning artifact:
- `EthicsCouncil/notes/REGIME_TRANSLATION_SPEC_V1.md`

Contents:
- domain -> regime mapping
- lens cluster -> controller archetype mapping
- caveats on non-equivalence

### Recommended next action 2
Create:
- `EthicsCouncil/notes/REGIME_BENCHMARK_PACK_V1.md`

Contents:
- selected case pack
- expected tensions
- what counts as meaningful evidence

### Recommended next action 3
Inspect `RegimeFrontierLab/scripts/` and `results/` to judge actual experimental maturity before drafting any glue code.

---

## Final recommendation

`RegimeFrontierLab` should currently be treated as an **offline calibration annex** for `EthicsCouncil`.

That is the highest-leverage, lowest-self-deception integration mode.

It strengthens anti-universalist discipline, tests regime fragility, and may reveal where existing lenses are robust or misaligned, without pretending that simulated frontiers can directly answer live ethical questions.
