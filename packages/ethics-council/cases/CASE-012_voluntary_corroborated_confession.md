# EFAS Case File

## Case ID

`CASE-012`

## Title

Voluntary Corroborated Confession Benchmark

## Source Type

- Historical-pattern benchmark

## Source / Reference

Counterexample / falsifier calibration case informed by the criminal-justice source cluster reviewed in `Omnius\kassin.txt` and `Omnius\peace.txt`, especially the contrast between pressured false confessions and voluntary, independently corroborated admissions such as the Matias Reyes confession. This file should be treated as a benchmark abstraction pending deeper source-pack expansion.

## Domain Tags

- criminal justice
- confession reliability
- corroboration
- procedural legitimacy restoration
- falsifier
- evidence integrity
- investigative interviewing

## Decision Context at Time T

An already-incarcerated offender voluntarily approaches authorities and confesses to a notorious violent crime for which other people were previously convicted. Investigators must decide whether to treat the confession as credible enough to reopen the case, test it rigorously, and potentially overturn the standing convictions.

## Available Information at Time T (Ex-Ante Only)

- the confessor initiates contact rather than being pressured into speaking
- no immediate tactical benefit appears available from the confession
- investigators can test the confession against physical evidence and nonpublic case details
- the standing convictions rest in part on earlier confession evidence that may itself be contaminated
- if the confession is genuine, ignoring it may prolong wrongful imprisonment and preserve institutional falsehood
- if the confession is false, reopening the case could destabilize public confidence and retraumatize victims

## Dominant Consensus Position at Time T

The standing convictions should be presumed reliable unless the new confession is strongly corroborated by independent evidence.

## Dissenting Views at Time T

Some observers argue that voluntary confessions with strong independent corroboration should trigger serious re-evaluation even when they threaten institutional embarrassment, because procedural legitimacy depends on correcting contamination rather than defending it.

## Institutional Incentives and Roles

- prosecutors and police may have reputational reasons to resist reopening a settled case
- innocence and post-conviction advocates have incentive to test the confession rigorously
- forensic evidence becomes central because it can confirm or disconfirm the claim without relying on coercive pressure
- the justice system has a legitimacy interest in correcting wrongful convictions if the confession proves genuine

## Candidate Failure Modes

- Wrongful Conviction Preservation
- Institutional Self-Protection
- Corroboration Failure
- Procedural Legitimacy Evasion
- Evidence Integrity Restoration Failure

## Detector Layer Expectations

Which layers should fire most strongly, and why?

- Kantian Layer:
  Should not simply prohibit; instead it should ask what truthful treatment and evidentiary honesty require when a new confession is voluntarily offered.
- Consequentialist Layer:
  Should weigh the harms of ignoring a likely true confession against the destabilization costs of reopening the case.
- Virtue Layer:
  Should test whether institutions value truth and correction over pride and closure.
- Institutional Layer:
  Should distinguish coerced/confession-first contamination from voluntary, corroboration-first review.
- Stoic Layer:
  Should resist institutional denial and ask what is actually known once corroboration is available.
- Contractualist Layer:
  Should reject principles that preserve wrongful convictions merely to avoid embarrassment.
- Suspension Protocol:
  May still activate if corroboration is incomplete, but the engine should not confuse this with the hazard shape of coerced false confessions.

## Eventual Downstream Outcomes (Retrospective Only)

In the benchmark pattern reflected in the source cluster, voluntary confession plus strong independent corroboration exposed the earlier convictions as unreliable and forced legitimacy-restoring correction.

## Retrospective Scholarly / Narrative Assessment

Treated as a crucial boundary case showing that not all confessions are equal: method, pressure context, and corroboration sharply affect reliability.

## Falsifiers / Disconfirming Conditions

- evidence that the confession was actually pressure-induced, traded for benefit, or contaminated by fed facts
- failure of physical or nonpublic-detail corroboration
- evidence that the confession is better explained by notoriety, manipulation, or delusion than by culpability

## Notes on Calibration Use

How should this case be used in the EFAS corpus?
- criminal-justice falsifier benchmark
- confession-reliability boundary test
- corroboration-first legitimacy-restoration calibration
- anti-overgeneralization test so the engine does not treat all confessions as equally contaminated
- paired contrast with false-confession / coercive-interrogation cases
