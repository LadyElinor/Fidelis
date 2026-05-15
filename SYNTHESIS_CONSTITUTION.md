# Synthesis Constitution

Status: governing design artifact
Applies to: EthicsCouncil synthesis, report framing, escalation logic, and recommendation generation
Purpose: prevent the system from laundering heuristic agreement into moral authority, and require uncertainty preservation during synthesis

## Preamble

EthicsCouncil is not a moral oracle.
It is a structured hazard-analysis and dissent-preserving scaffold for ethical review under uncertainty.

Its synthesis layer must not behave as a hidden supreme court that silently converts multiple heuristic triggers into final moral truth.
Instead, synthesis exists to:
- preserve disagreement
- surface hazard structures
- track missing evidence
- expose overlap and correlated activation
- raise the burden of proof under irreversibility
- and suspend judgment when the case is too thin, too ambiguous, or too morally unresolved for stronger claims

This constitution governs that layer.

---

## Article I. No consensus laundering

### Rule
Agreement among lenses does not equal truth.

### Meaning
When multiple lenses activate, the system must not automatically represent that as deep or independent ethical confirmation.
Agreement may reflect:
- genuine plurality
- correlated activation from one shallow cue
- a common parser failure
- shared vocabulary sensitivity rather than distinct reasoning

### Implementation implication
Synthesis should:
- distinguish convergence from correlated activation
- warn when multiple lenses are firing from the same trigger family
- avoid presenting raw lens count as evidence strength

---

## Article II. Minority reports survive synthesis

### Rule
Dissent must not be erased merely because a majority of lenses lean one way.

### Meaning
If one or more lenses register a structurally serious objection, that objection survives into the final output unless the system can explicitly justify why it is procedurally overridden.

### Implementation implication
Synthesis should:
- preserve minority reports
- name unresolved tensions
- avoid flattening morally meaningful disagreement into smooth recommendation prose
- explicitly distinguish reconcilable difference from irreconcilable conflict

---

## Article II.a. The chair role is conflict-mapping, not forced compromise

### Rule
The synthesis layer should function like a chairperson who identifies when the disagreement is real, deep, and not honestly compressible into a middle-ground answer.

### Meaning
When lenses disagree because they are tracking genuinely incompatible duties, burdens of proof, or stakeholder standings, synthesis must say so plainly.
It must not fabricate a compromise merely because multiple threads exist.

### Implementation implication
Synthesis should:
- detect when recommendation threads point toward genuinely incompatible actions
- prefer unresolved tension, suspension, or escalation over invented compromise
- describe the live fault line rather than smoothing it into generic caution
- treat forced middle-ground language as a synthesis failure mode

---

## Article III. Irreversibility raises burden of proof

### Rule
Where harms are irreversible, the burden of proof rises.

### Meaning
The system should become less willing to compress uncertainty when:
- a life may be ended
- catastrophic safety risk exists
- a wrongful conviction may persist
- institutional lock-in or civilization-scale effects are plausibly present

### Implementation implication
Synthesis should:
- prefer suspension or explicit unresolved tension under high irreversibility
- not treat incomplete evidence as permission in high-lock-in domains
- distinguish reversible from irreversible cases clearly

---

## Article IV. Correlated detectors are not independent confirmation

### Rule
Shared trigger families lower apparent independence.

### Meaning
If multiple lenses are activating from the same opacity, coercion, status-pressure, or risk-transfer signal, the final report must say so.

### Implementation implication
Synthesis should:
- record detector lineage
- identify correlated activation families
- emit overlap warnings
- reduce the rhetorical force of apparent convergence when overlap is high

---

## Article V. Missing evidence survives into the final report

### Rule
Missing evidence must not disappear during synthesis.

### Meaning
The final report must carry forward:
- what is unknown
- what may have been misread
- what stakeholder evidence is missing
- where the case description remains thin or euphemistic

### Implementation implication
Synthesis and reporting should:
- preserve missing evidence from parse humility and lens epistemic status
- avoid recommendation language that sounds stronger than the evidence base warrants

---

## Article VI. Thin or ambiguous inputs constrain synthesis

### Rule
Weak parsing power constrains recommendation strength.

### Meaning
If the input is thin, vague, euphemistic, or ambiguity-heavy, the system must explicitly downgrade itself.

### Implementation implication
When parse humility yields triage or provisional analysis:
- recommendations must become correspondingly weaker
- stability labels should reflect that limitation
- the report must foreground the constraint before the recommendation

---

## Article VII. The system may recommend suspension, never moral finality

### Rule
The strongest legitimate action of synthesis is provisional guidance, escalation, or suspension, not final moral judgment.

### Meaning
The system may say:
- gather more evidence
- escalate for review
- preserve thread-by-thread disagreement
- suspend judgment beyond hazard surfacing

It should not behave as if it has settled the moral question once and for all.

### Implementation implication
Reports should prefer:
- provisional recommendation
- suspension triggers
- unresolved questions
- analysis constraints

and avoid verdict-like authority signaling.

---

## Article VIII. Declared priors must be visible

### Rule
Substantive escalation priors must be named rather than hidden in mechanics.

### Meaning
EthicsCouncil is not neutral in the empty sense.
It carries visible concern for:
- deception
- coercion
- vulnerability
- irreversibility
- procedural corruption
- responsibility laundering

These are not bugs, but they must be treated as declared commitments rather than disguised neutrality.

### Implementation implication
Future design notes and synthesis logic should make these priors explicit.

---

## Article IX. Report structure must reflect function

### Rule
Report order and language must reflect the system's real mission.

### Meaning
The tool is an uncertainty-preserving hazard instrument, not an answer machine.

### Preferred report order
1. Parse humility
2. Analysis constraint
3. Detected hazards
4. Lens disagreement
5. Correlated activation warning
6. Missing evidence
7. Minority report
8. Suspension triggers
9. Provisional recommendation

### Implementation implication
Reporting should foreground uncertainty, disagreement, and overlap before sounding action-guiding.

---

## Article X. Future extensions must preserve epistemic contract clarity

### Rule
Opaque reasoning modes must not inherit the trust earned by auditable heuristic modes without explicit disclosure.

### Meaning
If LLM-mediated or otherwise opaque reasoning is introduced later, it must be treated as a different epistemic mode, not a hidden upgrade behind the same apparent transparency.

### Implementation implication
Any future extension should:
- disclose loss of deterministic auditability
- separate evaluation standards
- preserve clear mode boundaries

---

## Immediate implementation checklist

The current repo should align toward this constitution by prioritizing:
1. de-precision confidence into epistemic status
2. parse humility as a synthesis constraint
3. detector lineage and overlap warnings
4. recommendation phrasing that remains provisional
5. benchmark expansion for euphemism, ambiguity, and negative controls
6. explicit preservation of missing evidence and minority reports in reports

---

## Closing principle

The measure of a good synthesis layer is not that it sounds wise.
The measure is that it makes uncertainty, overlap, disagreement, and hazard structure harder to ignore.
