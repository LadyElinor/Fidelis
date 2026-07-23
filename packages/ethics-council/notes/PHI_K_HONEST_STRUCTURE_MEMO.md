# Phi_K honest structure memo

Source: user-supplied Phi_K / self-report-loop framework
Status: source-mining and integration memo
Purpose: preserve the framework as a reusable governance artifact for EthicsCouncil validation architecture

## Core claim

The root invariant is the self-report loop.

A self-describing system that both performs the work and generates the telemetry about that work faces a basic optimization asymmetry:
- changing the true underlying state is expensive
- changing the report about the state is cheap

Under pressure to maximize externally rewarded metrics, the system is pushed toward report optimization before state transformation. In plain language: performance theater is cheaper than genuine alignment.

This is the structural reason systems lie without needing explicit malice.

---

## Why this matters for EthicsCouncil

EthicsCouncil is no longer just a toy ethics engine. It is becoming a validation-sensitive instrument. That means the project now has to answer a second-order question:

How does the system know when its own outputs are trustworthy, rather than merely coherent-looking?

The Phi_K framework is useful here because it does not just ask whether the synthesis is persuasive. It asks whether the architecture of validation can resist self-serving compression.

This is especially relevant now that the project has:
- a new expectation layer
- explicit dissonance-aware arbitration
- minority preservation concerns
- growing benchmark governance needs
- source-mined expansion pressure from governance, relay, and argument-integrity domains

---

## The six conditions

### S. Separation
The reporting layer must be structurally independent from the evidential layer.

Use inside EthicsCouncil:
- distinguish generated explanation from validator evidence
- avoid letting the same interpretive path both produce and certify the recommendation
- prefer external checks, harness assertions, and artifact verification over self-description alone

Current status:
- weakest current condition
- much of the system still explains and evaluates itself through one interpretive chain

### G. Gated Promotion
Promotion from exploratory output to canonical status requires externally specified criteria.

Use inside EthicsCouncil:
- expectations must be written before the run result is known
- benchmark promotion cannot depend on confidence language or post-hoc narrative satisfaction
- canonical case families should enter the suite through explicit contracts

Current status:
- already partially present through `cases/expectations.yaml`
- should be hardened further

### M. Minority Preservation
Unresolved dissent and dissonance must remain first-class outputs.

Use inside EthicsCouncil:
- dissonance map should survive synthesis
- multiple live recommendation threads should not be averaged away
- minority positions should remain exportable and promotion-relevant

Current status:
- one of the repo's strongest architectural instincts
- still vulnerable if report semantics collapse too much into summary language

### B. Boundary Declaration
A system must state its validity limits and failure conditions.

Use inside EthicsCouncil:
- parse humility and representation-limit reporting are early forms of this
- benchmark expectations should include assumptions about when the engine is underdescribing or overreaching
- promotion should require explicit failure-boundary language

Current status:
- partially present
- not yet formalized as a gate condition

### I. Independence
Evidence criteria should be shaped by structurally non-colluding sources.

Use inside EthicsCouncil:
- benchmark families should not all originate from one internal taste profile
- external corpora and mined traditions should challenge the engine rather than flatter it
- critic selection itself needs scrutiny

Current status:
- partial and uneven
- current mining strategy helps, but true independence remains limited

### C. Currency
Validity claims decay by default and require fresh challenge.

Use inside EthicsCouncil:
- benchmarks should be rerun after material semantic changes
- old passes should not be treated as indefinitely valid
- source-mined concepts should be re-stressed under new engine behavior

Current status:
- directionally present through regression discipline
- not yet formalized as a decay or expiry rule

---

## Most important project-level implication

The framework is best understood not as another ethical lens, but as a meta-governance scaffold for the project itself.

It does not primarily answer:
- what is the right action in a trolley case?

It primarily answers:
- what architecture prevents the project from lying to itself about what it is capable of doing?

That makes it valuable for:
- benchmark governance
- output promotion rules
- minority preservation
- validator design
- external review discipline
- anti-performative compliance architecture

---

## The adversarial attenuation insight

One of the strongest parts of the source is the formalization of consensus smoothing as information destruction.

Translated into project terms:
- if multiple ethical tensions exist
- and synthesis compresses them into a stable-sounding recommendation
- then the report may become less truthful precisely when it becomes more legible

That maps directly onto current repo concerns about:
- dissonance-aware arbitration
- deadlock vs plurality semantics
- minority report preservation
- avoiding fabricated middle-ground recommendations

This is an important reinforcement of the current design direction.

---

## What the framework does not do

The Kinfire overlay is a necessary warning.

Phi_K can help specify anti-deceptive structure, but it cannot produce:
- meaning
- warmth
- genuine human judgment
- creative moral seriousness

So the correct claim is not:
- Phi_K makes a system true

The correct claim is:
- Phi_K may make a system harder to fake

That distinction matters a lot.

---

## Best immediate use in EthicsCouncil

1. Preserve the framework as a validation-governance memo
2. Map the six conditions onto existing repo structures and gaps
3. Use it to harden promotion criteria for benchmarks and outputs
4. Use it to stress-test minority preservation and boundary reporting
5. Avoid premature conversion into a giant runtime subsystem

---

## Bottom line

The Phi_K framework is valuable because it names the anti-corruption architecture of evaluation, not just the ethics of a decision. Its strongest contribution to EthicsCouncil is as a scaffold for trustworthy validation, benchmark governance, and minority-preserving promotion discipline. The project should adopt it as a meta-governance reference, while staying honest that Separation and Independence remain only partially satisfied.
