# Actuarial risk ethics memo

Primary source basis: `Omnius\actu.txt` (introductory actuarial science and actuarial mathematics material)
Secondary support: `Omnius\ra.txt` (modern risk-analysis summary and synthesis)
Status: calibration memo
Use: sharpen institutional, trustee, contractual, and vulnerability-aware analysis where quantified risk management shapes real human exposure

## Why this source is worth using

Actuarial material does not primarily contribute a new moral philosophy. Its value is different.
It shows how institutions:
- quantify uncertainty
- price exposure
- maintain reserves and solvency
- convert individual vulnerability into pooled abstractions
- distinguish technical adequacy from equitable treatment only imperfectly

That makes it useful as a calibration source for cases where procedural, pricing, or solvency logic can appear rational while concealing ethically important remainder.

---

## Core usable ethical primitives

### 1. Adequacy is not equity
Actuarial systems can be technically adequate for solvency, reserves, or premium sufficiency while still distributing burdens inequitably.

Usable engine question:
- Is this arrangement merely adequate for system stability, or also equitable in how it allocates burdens, exclusions, and protection?

### 2. Actuarial equivalence is not moral equivalence
A mathematically fair premium or reserve relationship does not automatically settle whether the resulting arrangement is ethically fair.

Usable engine question:
- Is numerical equivalence being mistaken for moral fairness?

### 3. Aggregate rationality can conflict with claimant-level justice
Portfolio-level prudence may be coherent in the aggregate while leaving particular people exposed to severe hardship, exclusion, or under-recognition.

Usable engine question:
- Does aggregate optimization hide unjust treatment at the level of the actual person who must bear the consequence?

### 4. Model choice is not morally neutral
Deterministic versus stochastic framing, tail assumptions, category design, and data selection influence who is visible, who is costly, and what counts as prudent.

Usable engine question:
- Which moral choices are being smuggled into model assumptions and treated as if they were purely technical?

### 5. Solvency stewardship is real but incomplete
Insurers and pooled-risk institutions do have genuine duties to preserve reserves and avoid ruin. That duty is ethically important, but it does not override all fairness concerns automatically.

Usable engine question:
- Is solvency being treated as one fiduciary duty among others, or as a total excuse for harsh exclusion or burden shifting?

### 6. Quantification can erase lived remainder
What is measurable in pricing, reserving, and expected-loss modeling may omit humiliation, dependency, fear, disrupted life plans, or asymmetric bargaining vulnerability.

Usable engine question:
- What morally serious residue is being left outside the model because it is hard to quantify?

### 7. Risk transfer can be technically clean and ethically dirty
Insurance, indemnity, and reserve logic can make a transfer of exposure legible and financeable without making it just.

Usable engine question:
- Has technical risk transfer clarity outrun fair responsibility allocation?

---

## Good uses in EthicsCouncil

### Strongest fit
- `institutional`
- `trustee`
- `contractualist`
- some `care_ethics`

### Best case types
- underwriting fairness
- reserve / solvency trade-off decisions
- pricing exclusions
- hold-harmless and indemnity structures
- claims practices shaped by aggregate portfolio logic
- catastrophic or tail-risk governance
- model opacity and quantified decision systems

---

## Main warnings

1. do not confuse actuarial rigor with moral sufficiency
- better measurement is not the same thing as better justice

2. do not swing to anti-quantification romanticism
- pooled-risk systems really do require disciplined modeling

3. preserve the difference between pool stewardship and opportunistic exclusion
- prudence and profiteering can look superficially similar

4. avoid importing domain machinery wholesale
- the engine needs a few sharp concepts, not an insurance textbook

---

## Narrow patch directions

### Patch candidate A
Add synthesis note trigger:
- `actuarial_fairness_gap_risk`

Definition:
- quantified, actuarially disciplined, or solvency-oriented reasoning appears to be standing in for a broader fairness judgment it does not actually settle

### Patch candidate B
Add synthesis note trigger:
- `aggregate_rationality_vs_individual_justice_risk`

Definition:
- portfolio, system, or reserve logic appears coherent in aggregate while imposing ethically underexamined hardship or exclusion on identifiable persons or weaker parties

### Patch candidate C
Strengthen `institutional` concern language for:
- model assumptions treated as neutral despite distributive consequences
- technical adequacy being overread as ethical adequacy

### Patch candidate D
Strengthen `trustee` concern language for:
- solvency stewardship invoked sincerely but too totalistically, crowding out duties of fair treatment and responsible burden allocation

### Patch candidate E
Strengthen `care_ethics` concern language for:
- the lived human residue excluded by quantitative abstraction

---

## Preferred implementation order

1. memo only
2. if patching, start with `actuarial_fairness_gap_risk`
3. only then consider `aggregate_rationality_vs_individual_justice_risk`
4. do not add a large standalone insurance lens

---

## Bottom line

The ethical lesson of actuarial reasoning is not that quantification is bad. It is that institutions often mistake quantified prudence for full moral adequacy. Actuarial clarity can discipline judgment, but it can also conceal what remains unfair, unshared, or humanly devastating at the point where the model cashes out in a real life.
