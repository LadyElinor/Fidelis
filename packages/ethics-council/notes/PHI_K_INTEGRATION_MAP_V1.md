# Phi_K integration map v1

Purpose: map the Phi_K honest-structure framework onto current EthicsCouncil mechanisms, strengths, gaps, and likely next uses.

## Summary judgment

Phi_K fits EthicsCouncil best as a validation and governance layer, not as an immediate first-pass runtime moral detector.

Its role is to audit the conditions under which the repo should trust its own outputs.

---

## Condition-by-condition map

### S. Separation
Definition:
- reporting must be structurally distinct from evidential validation

Current partial equivalents:
- regression harness checks expectations independently of freeform narrative
- file artifacts and benchmark prompts exist outside model-produced explanation text

Current gap:
- the same engine still produces both the recommendation and much of the interpretation of whether that recommendation is coherent
- runtime explanations remain too close to self-description

Best next use:
- continue increasing the role of external harness assertions
- prefer structured fields over prose when validating behavior
- eventually separate evaluator-of-output logic more sharply from output-generation logic

### G. Gated Promotion
Definition:
- promotion requires precommitted criteria not generated from the system's own confidence

Current partial equivalents:
- `cases/expectations.yaml`
- explicit benchmark families and regression slices

Current strength:
- this is already emerging as one of the clearest advances in the project

Best next use:
- require all new canonical case families to ship with expectations
- distinguish exploratory cases from promotion-eligible cases
- avoid upgrading semantics based on narrative plausibility alone

### M. Minority Preservation
Definition:
- unresolved dissent must remain exportable and promotion-relevant

Current partial equivalents:
- dissonance-aware arbitration
- dissonance map
- minority report logic
- anti-compression recommendation language

Current strength:
- one of the repo's best instincts

Current risk:
- summary semantics can still flatten living variance into stable-sounding recommendation text
- Dung plurality and deadlock language can blur rather than clarify if not tightly scoped

Best next use:
- preserve live fault lines in outputs
- make canonical conflict structures promotion-blocking when appropriate
- keep deadlock semantics narrower and more honest

### B. Boundary Declaration
Definition:
- the system must publish where its claims stop holding

Current partial equivalents:
- parse humility
- representation-limit assessment
- unresolved questions

Current gap:
- these boundary statements are present, but not yet decisive promotion gates
- boundary language is sometimes descriptive rather than operational

Best next use:
- connect analysis-mode and representation limits to benchmark governance
- require explicit boundary statements for major promoted outputs
- define clearer collapse conditions for known blind spots

### I. Independence
Definition:
- evidence criteria should be set by non-colluding sources

Current partial equivalents:
- source mining from external corpora
- governance, relay, and argument-integrity benchmark expansion from heterogeneous materials

Current gap:
- source selection still occurs within a fairly unified operator frame
- critic families and mined domains may still reflect local taste more than true adversarial independence

Best next use:
- continue diversifying benchmark source families
- explicitly document where adversarial review is still internally curated
- keep an eye on performative dissent that flatters rather than stresses the engine

### C. Currency
Definition:
- validation claims decay and require fresh challenge

Current partial equivalents:
- rerunning focused slices after semantic changes
- using regression as a live contract rather than a one-time proof

Current gap:
- no explicit expiry or decay schedule for benchmark confidence
- no formal rule that past passes lose authority after major architecture shifts

Best next use:
- define when semantic changes invalidate previous confidence
- treat benchmark passes as time-bounded evidence
- refresh key slices after each major synthesis or detector change

---

## Where Phi_K reinforces current project direction

The framework strongly supports the recent project shift toward:
- calibration before expansion
- expectations before architecture growth
- minority preservation before summary neatness
- source-mined validation before new detector proliferation
- semantic cleanup before confidence inflation

That is a strong sign of fit.

---

## Where Phi_K exposes the harshest weaknesses

### Weakest condition now: Separation
The repo still relies heavily on an engine that explains its own behavior from within the same interpretive machinery.

### Second weakest: Independence
Benchmarks are getting more diverse, but the adversarial ecosystem is still relatively local and curated.

### Most advanced condition: Minority Preservation
The repo is already unusually aligned with this condition in spirit, though implementation details still need hardening.

---

## Recommended uses right now

### Immediate
- cite Phi_K in notes/governance artifacts
- use it to justify expectation-led promotion discipline
- use it to evaluate whether dissonance is truly being preserved

### Near-term
- create a lightweight benchmark-promotion checklist derived from S/G/M/B/I/C
- apply it to new benchmark families before canonization

### Not yet
- do not turn Phi_K into a broad runtime score or one more detector family
- do not claim full compliance where only partial custody separation exists

---

## Practical translation into repo questions

When adding or revising any major mechanism, ask:
- Separation: is the validator independent from the narrative it is checking?
- Gated Promotion: were success criteria fixed before seeing the result?
- Minority Preservation: did dissent survive as a first-class output?
- Boundary Declaration: did we state where the claim fails?
- Independence: who benefits from the validator saying yes?
- Currency: how stale is the evidence that this still works?

---

## Bottom line

Phi_K should be treated as a meta-governance reference for how EthicsCouncil validates itself. It does not replace ethical lenses. It regulates when outputs deserve trust, when promotion should halt, and where the project is still vulnerable to performance theater masquerading as rigor.
