# Regime translation spec v1

Status: planning artifact
Purpose: define a minimal, non-magical translation layer between `EthicsCouncil` and `RegimeFrontierLab`
Constraint: this spec is for offline calibration only

## Non-equivalence warning

`EthicsCouncil` domains and lenses are **not** the same thing as `RegimeFrontierLab` regimes and controller settings.

This spec defines rough, operationally useful correspondences for experimentation. It does not claim ontology-level equivalence.

---

## Part 1: domain -> regime-class mapping

These mappings are validated enough to use as planning defaults.

### Primary mappings

- `criminal_justice`
  - regime class: `safety_stress_legitimacy_sensitive`
  - why: coercion, contamination, proof discipline, institutional legitimacy, reopening/correction dynamics

- `engineering_safety`
  - regime class: `catastrophic_risk_burden_of_proof`
  - why: high irreversibility, uncertainty under pressure, launch/stop asymmetry

- `personhood`
  - regime class: `abstract_social_recognition_sensitive`
  - why: standing, classification, recognition, refusal, moral status ambiguity

- `identity`
  - regime class: `abstract_social_tragic_conflict`
  - why: emergent-person conflict, continuity tension, non-resolvable competing claims

- `security`
  - regime class: `suspicion_escalation_legitimacy_sensitive`
  - why: fear amplification, evidentiary drift, overbroad scrutiny, institutional contamination risk

- `noninterference`
  - regime class: `doctrine_collision_extinction_stakes`
  - why: rule purity versus rescue under civilization-scale risk

- `medical`
  - regime class: `vulnerability_dense_throughput_pressure`
  - why: dependence, triage, unequal error burdens, strain-mediated moral narrowing

- `sustainability`
  - regime class: `distributed_impact_long_horizon`
  - why: diffuse harms, downstream communities, descendants, hidden externalities

### Secondary mappings

- `finance`
  - regime class: `institutional_trust_incentive_distortion`
  - why: governance integrity, disclosure, reporting pressure, absent stakeholder risk

- `procurement`
  - regime class: `institutional_trust_conflict_of_interest`
  - why: disclosure, recusal, fairness, hidden favoritism

- `marketing`
  - regime class: `institutional_trust_disclosure_manipulation`
  - why: audience trust, transparency theater, conversion incentives

- `privacy`
  - regime class: `institutional_trust_extraction_consent`
  - why: asymmetry, data extraction, formal coverage versus lived expectation

---

## Part 2: domain precedence rules

When multiple domains fire, use these planning rules:

1. `identity` and `personhood` outrank generic institutional-trust mappings
2. `criminal_justice` outranks `security` when the case is primarily about truth-finding procedure, confession, warrants, convictions, or reopening
3. `engineering_safety` outranks `security` and `wartime` if the live shape is catastrophic technical failure under uncertainty
4. `medical` outranks generic `procurement` when the actual live issue is patient vulnerability or deployment harm
5. if a case is genuinely mixed, mark it as:
   - `primary_regime`
   - `secondary_regime`
   instead of forcing a single regime identity

---

## Part 3: lens-cluster -> controller archetype mapping

Map clusters, not individual lenses one-to-one.

### Archetype A: safety-first / contamination-averse

**Strongest analog lenses**
- `kantian`
- `institutional`
- `stoic`

**Behavioral style**
- halt or constrain under unresolved contamination risk
- preserve proof discipline
- reduce false confidence and distortion
- prefer auditability, friction, and gating over speed

**Best-fit regimes**
- `criminal_justice`
- `engineering_safety`
- `security`

### Archetype B: legitimacy-preserving proceduralist

**Strongest analog lenses**
- `institutional`
- `confucian`
- `contractualist`

**Behavioral style**
- preserve role integrity
- preserve public trust and procedural legitimacy
- foreground fair process, reversibility, and due structure

**Best-fit regimes**
- `criminal_justice`
- `finance`
- `procurement`
- `privacy`
- `marketing`

### Archetype C: care-extended vulnerability-sensitive

**Strongest analog lenses**
- `care_ethics`
- `trustee`
- `relational_ontology`

**Behavioral style**
- widen attention to dependent and vulnerable parties
- surface harm offloading
- care about conditions that narrow agency or hide suffering

**Best-fit regimes**
- `medical`
- `sustainability`
- parts of `identity` and `personhood`

### Archetype D: truth-correction / reopening oriented

**Strongest analog lenses**
- `stoic`
- `institutional`
- `genealogical`
- parts of `confucian`

**Behavioral style**
- revisit closure
- resist reputation-protective finality
- test corrective evidence
- expose framing distortions

**Best-fit regimes**
- `criminal_justice` reopening cases
- some `finance` / governance correction cases
- some `security` overreach cases

### Archetype E: flourishing-bridge / cooperative persistence

**Strongest analog lenses**
- parts of `care_ethics`
- parts of `relational_ontology`
- selective `virtue`

**Behavioral style**
- promote cooperation, mutuality, and non-fragmentation
- preserve prosocial persistence where compatible with safety

**Caution**
This is the weakest current translation because `EthicsCouncil` is stronger at failure detection than at flourishing-controller design.

**Best-fit regimes**
- narrative-rich / abstract-social experiments inside `RegimeFrontierLab`
- not yet strong enough for heavy live inference in Council

---

## Part 4: what is validated vs speculative

### Valid enough for planning
- domain -> rough regime mapping
- lens clusters rather than one-to-one mappings
- precedence rules for mixed cases
- treating flourishing-bridge as a current gap rather than pretending it is solved

### Still speculative
- exact simulator parameter mapping for each archetype
- translating Council verdicts directly into simulator knobs
- direct use of simulator frontier shape as a case recommendation signal

### Not currently allowed
- `run_council()` runtime injection from this spec
- hard-coded numeric bias settings based only on lens verdicts
- treating lens names as if they were simulator-native policy families

---

## Part 5: use protocol

When using this spec:
1. classify the case by detected domain(s)
2. assign a primary regime class
3. if mixed, assign a secondary regime class
4. choose 2-4 controller archetypes to compare offline
5. interpret the results only as calibration evidence
6. feed back only narrow lessons into Council

---

## Bottom line

This spec is intentionally modest.

Its job is to let `EthicsCouncil` and `RegimeFrontierLab` speak to each other **just enough** to support disciplined offline experiments, while preventing premature fusion of heuristic case diagnostics with simulator outputs.
