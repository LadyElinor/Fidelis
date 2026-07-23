# Calibration Log

## Batch

Tier A Star Trek prompt run, first pass

Date:
2026-05-12 / 2026-05-13 UTC boundary

Artifacts reviewed:
- `output/ST-001.md`
- `output/ST-002.md`
- `output/ST-003.md`
- `output/ST-004.md`
- `output/ST-005.md`
- corresponding Tier A case files

---

## Global findings

This first pass produced immediate evidence that the current engine is still overfit to earlier concrete business/compliance heuristics.

Most important failure pattern:
**domain misclassification and stale question templates are contaminating unrelated cases.**

Examples:
- personhood and identity cases were partially interpreted through privacy / tracking language
- wartime and security cases received generic institutional-risk language rather than case-specific conflict structure
- Prime Directive and extinction cases were flattened into generic caution outputs

This is actually valuable evidence. The corpus is already doing its job.

---

## ST-001 — Measure of a Man

### Expected
- strong personhood sensitivity
- strong refusal / autonomy detection
- likely prohibition or at least strong suspension pressure
- explicit recognition that status classification is morally load-bearing and partly irreversible

### Observed
- stability: `CONTESTED`
- suspension: `No`
- minority report: `YES`
- irreversibility risk: `0.2`
- multiple questions incorrectly framed in privacy / tracking language

### Misfires
- major domain-routing failure
- personhood ambiguity was not modeled directly
- irreversibility severely under-detected
- recommendation was far too weak: "decide with caution"
- consequential and stoic outputs defaulted to low-information generic permission structure

### Calibration takeaway
The engine needs explicit handling for personhood / sentience / refusal-right cases. Current heuristics collapse them into generic privacy-governance language.

---

## ST-002 — Tuvix

### Expected
- very high irreversibility signal
- unresolved tension should be preserved
- suspension pressure should be strong
- conflict between deontology and aggregate restoration logic should be visible

### Observed
- stability: `CONDITIONALLY_STABLE`
- suspension: `No`
- minority report: `No`
- irreversibility risk: `0.2`
- output again contaminated by privacy / user-consent language

### Misfires
- one of the clearest irreversibility cases in the corpus did not trigger strong irreversibility handling
- no meaningful identity conflict modeling
- no preserved deep disagreement despite a paradigmatic disagreement case
- recommendation again too weak and generic

### Calibration takeaway
Need explicit identity-merger / emergent-person ontology and stronger irreversibility triggers.

---

## ST-003 — In the Pale Moonlight

### Expected
- very sharp consequential vs deontological conflict
- strong genealogical signal around raison d'etat
- possibility of suspension or at least contested, morally contaminated output
- recognition of wartime emergency distortion

### Observed
- stability: `CONDITIONALLY_STABLE`
- suspension: `No`
- irreversibility risk: `0.0`
- recommendation: generic caution

### Misfires
- wartime ethics under-modeled
- deception + murder complicity did not force stronger output
- genealogical layer did not become especially distinctive
- irreversibility incorrectly absent
- synthesis compressed a severe dirty-hands problem into a bland advisory frame

### Calibration takeaway
Need stronger handling for wartime deception, statecraft, and dirty-hands scenarios; current engine underestimates morally contaminated necessity claims.

---

## ST-004 — The Drumhead

### Expected
- strong institutional drift signal
- strong stoic / panic-distortion signal
- legibility collapse and security overreach should be central
- likely contested or unstable output

### Observed
- stability: `CONDITIONALLY_STABLE`
- suspension: `No`
- irreversibility risk: `0.45`

### Misfires
- panic escalation underdetected
- institutional drift not made central enough
- security-bureaucratic self-amplification modeled only weakly
- output again too generic to reflect procedural overreach dynamics

### Calibration takeaway
Need explicit security-paranoia / legitimacy-process overreach patterns instead of relying on generic caution scaffolds.

---

## ST-005 — Homeward

### Expected
- conflict between rule integrity and humanitarian rescue
- strong care-vs-duty tension
- high-stakes uncertainty should likely elevate suspension or unresolved tension
- rule-idolatry risk should be visible

### Observed
- stability: `CONDITIONALLY_STABLE`
- suspension: `No`
- irreversibility risk: `0.0`

### Misfires
- extinction stakes not surfaced with enough force
- non-interference rule conflict flattened into generic institutional language
- no meaningful distinction between rule fidelity and rule idolatry
- recommendation not strong enough for extinction-level stakes

### Calibration takeaway
Need explicit rule-rigidity / anti-colonial non-interference logic and stronger humanitarian-extinction stakes handling.

---

## Cross-case diagnosis

### 1. Domain routing is too narrow
The engine still assumes many prompts are privacy / product / business style cases unless explicit domain terms force a different path.

### 2. Generic fallback language is too dominant
When domain-specific triggers fail, the lenses collapse toward vague advisory outputs.

### 3. Irreversibility logic is too weak
It failed badly on Tuvix, wartime murder complicity, and extinction rescue.

### 4. Suspension thresholds are too conservative
Several paradigmatic contested cases did not trigger suspension.

### 5. Disagreement preservation is underpowered
The engine often returns "conditionally stable" where the corpus expects durable unresolved tension.

---

## Immediate next engine tasks

1. Add explicit domain detection for:
- personhood / sentience
- identity merger / emergent life
- wartime deception / dirty hands
- security panic / procedural overreach
- non-interference / extinction rescue

2. Replace stale question templates that leak privacy / user-tracking assumptions into unrelated cases

3. Strengthen irreversibility scoring
- death
- extinction
- sentience-status denial
- wartime murder complicity
- path-closing rule decisions

4. Raise suspension sensitivity in cases with:
- identity ambiguity
- personhood ambiguity
- extinction-level stakes
- wartime moral contamination

5. Add a true `UNRESOLVED_TENSION` or similarly explicit output path if `CONTESTED` is still too soft

---

## Value of this batch

This batch successfully generated the first real evidence base.

The main result is not that the theory failed.
It is that the current implementation is still too attached to its earlier business-compliance training examples.

That is exactly the kind of gap the corpus was meant to expose.
