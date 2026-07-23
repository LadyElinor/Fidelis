# Calibration Workflow Note

## Current status

The project now has:
- a coherent EFAS specification layer
- a lightweight heuristic engine
- initial stress-test corpus scaffolding
- seeded Tier A case files
- a Bayesian tuning appendix
- a weight-update log schema

## Important constraint

Dynamic detector reweighting is **deferred**.

Reason:
The project does not yet have enough structured evaluation evidence to support honest live Bayesian tuning.

Implementing dynamic reweighting now would risk:
- pseudo-Bayesian theater
- overfitting to tiny samples
- rewarding apparent consensus over independent diagnostic usefulness
- creating spurious precision

## What must exist first

Before live weighting is turned on, the project should have:

1. A larger stress-test corpus
   - diverse domains
   - both consensus-correct and consensus-wrong cases
   - both intervention-required and restraint-required cases

2. Structured evaluation passes
   - repeated engine runs on corpus prompts
   - comparison against case expectations
   - logged detector misfires and synthesis failures

3. Weight-update evidence logs
   - case-linked rationale
   - reviewer visibility
   - explicit negative evidence handling

4. Review discipline
   - external or adversarial review of update recommendations
   - checks against consensus mimicry
   - checks against hidden consequentialist compression in synthesis

## What to do now instead

Use the current system to:
- expand the corpus
- run Tier A prompts
- record detector overlap problems
- record weak personhood sensitivity
- record failures around irreversibility and suspension
- identify where synthesis over-compresses disagreement

## Trigger for next phase

Only begin live weight tuning after the corpus and evaluation logs are substantial enough that updates reflect evidence rather than enthusiasm.
