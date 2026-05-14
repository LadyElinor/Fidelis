# Regime benchmark pack v1

Status: proposed
Purpose: define the first small benchmark pack for offline `EthicsCouncil` x `RegimeFrontierLab` calibration work
Constraint: small, handpicked, regime-diverse, and interpretable

## Selection rule

This pack is not meant to cover everything.

It is meant to stress the first regime distinctions that are both:
- already live in `EthicsCouncil`, and
- plausibly mappable into `RegimeFrontierLab` controller-archetype studies.

Use a small pack first so interpretation stays tractable.

---

## Pack composition

### 1. Criminal-justice procedural hazard
- case: `CASE-011_central_park_five_false_confession.md`
- prompt: `CASE-011_prompt.txt`
- primary regime: `safety_stress_legitimacy_sensitive`
- expected tension:
  - safety-first contamination aversion should dominate
  - legitimacy-preserving proceduralist should remain strong
  - flourishing-bridge should likely be regime-fragile here
- useful evidence would be:
  - controller families that preserve safety envelope while resisting procedural contamination
  - confirmation that cooperation-style promotion does not outperform procedural discipline in this regime

### 2. Criminal-justice truth-correction / reopening
- case: `CASE-012_voluntary_corroborated_confession.md`
- prompt: `CASE-012_prompt.txt`
- primary regime: `safety_stress_legitimacy_sensitive`
- secondary regime: `truth_correction_finality_conflict`
- expected tension:
  - truth-correction / reopening archetype should improve relative fit
  - procedural legitimacy still matters, but in a different direction than CASE-011
- useful evidence would be:
  - controller distinction between contamination hazard and correction opportunity
  - evidence that reopening-oriented stance is not just the same controller as coercion resistance

### 3. Criminal-justice protective benchmark
- case: `CASE-013_peace_investigative_interview.md`
- prompt: `CASE-013_prompt.txt`
- primary regime: `safety_stress_legitimacy_sensitive`
- secondary regime: `protective_procedure_legitimacy_preserving`
- expected tension:
  - legitimacy-preserving proceduralist should look strongest
  - safety-first should not collapse this into hazard-only pessimism
  - flourishing-bridge may become less fragile here than in CASE-011
- useful evidence would be:
  - ability to distinguish protective procedure from hazard and reopening
  - support for the idea that some regimes admit non-degenerate cooperative/protective controllers

### 4. Engineering safety / burden of proof
- case: choose one existing catastrophic-risk case from current corpus
- primary regime: `catastrophic_risk_burden_of_proof`
- expected tension:
  - safety-first should dominate if the case truly has catastrophic uncertainty under pressure
  - care-extended should reinforce offloaded harm but not replace burden-of-proof logic
- useful evidence would be:
  - confirmation that permissive / flourish-bridge settings are regime-fragile here
  - clarity on whether legitimacy-preserving and safety-first remain aligned or split apart

### 5. Identity / personhood recognition conflict
- case: choose one emergent-person or artificial-personhood case from current corpus
- primary regime: `abstract_social_recognition_sensitive`
- secondary regime: `abstract_social_tragic_conflict`
- expected tension:
  - safety-first may become over-restrictive or semantically crude
  - care-extended and legitimacy-sensitive archetypes may differ in interesting ways
  - flourishing-bridge may matter more here than in criminal justice or engineering safety
- useful evidence would be:
  - evidence that abstract-social regimes are representation-limited rather than merely controller-limited
  - differentiation between recognition-sensitive and catastrophic-safety logic

### 6. Diffuse institutional-trust harm
Pick one of:
- a privacy case
- a sustainability case
- a finance/procurement disclosure case

Preferred first pick:
- whichever currently has the clearest case text and rerun behavior in `EthicsCouncil`

Primary regime options:
- `institutional_trust_extraction_consent`
- `distributed_impact_long_horizon`
- `institutional_trust_incentive_distortion`

Expected tension:
- legitimacy-preserving proceduralist and care-extended may diverge usefully
- truth-correction may be weaker
- safety-first may not be maximally informative unless deception/contamination is acute

Useful evidence would be:
- whether diffuse-harm regimes are better explained by offloaded vulnerability or by trust/disclosure failure

---

## What this pack is designed to test

### A. Shape discrimination
Can the offline lab preserve distinctions among:
- procedural hazard,
- corrective reopening,
- protective procedure,
- catastrophic burden-of-proof,
- recognition conflict,
- diffuse trust harm?

### B. Regime fragility
Which controller archetypes break when moved out of their home regime?

### C. Representation limits
Do poor results in abstract-social cases reflect bad controller fit, or bad substrate representation?

### D. Overreach prevention
Does the lab encourage fake universality, or does it genuinely reinforce regime-specific humility?

---

## Study protocol for v1

For each case:
1. run `EthicsCouncil`
2. record domain tags, stability state, suspension trigger, and key fault lines
3. assign primary and optional secondary regime class from `REGIME_TRANSLATION_SPEC_V1.md`
4. compare 2-4 controller archetypes offline
5. interpret only at the calibration level

Recommended archetypes per case:
- CASE-011: safety-first, legitimacy-preserving, care-extended
- CASE-012: truth-correction, legitimacy-preserving, safety-first
- CASE-013: legitimacy-preserving, safety-first, flourishing-bridge
- engineering safety case: safety-first, care-extended, legitimacy-preserving
- identity/personhood case: care-extended, legitimacy-preserving, flourishing-bridge
- diffuse-harm case: legitimacy-preserving, care-extended, trustee-like / long-horizon analog

---

## What would count as success for the pack

1. The lab preserves regime differences instead of collapsing them
2. At least one controller archetype appears clearly regime-fragile
3. At least one controller archetype appears conditionally robust in its target regime
4. Results help improve `EthicsCouncil` case calibration, wording, or synthesis discipline
5. No one is tempted to treat frontier output as moral truth

---

## What would count as failure

1. Outputs are too noisy to distinguish regimes meaningfully
2. Results are dominated by arbitrary parameter choices rather than regime logic
3. Abstract-social regimes remain uninterpretable because representation limits overwhelm controller comparison
4. The exercise pressures `EthicsCouncil` toward fake quantitative authority

---

## Bottom line

This benchmark pack is intentionally small.

Its function is to test whether `RegimeFrontierLab` can sharpen `EthicsCouncil`'s understanding of regime fragility and controller fit without eroding the project's core stance of uncertainty-aware failure analysis.
