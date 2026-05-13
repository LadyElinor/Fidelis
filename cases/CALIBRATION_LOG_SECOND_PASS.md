# Calibration Log, Second Pass

## Batch

Tier A Star Trek prompt rerun after domain-routing and synthesis patch

Date:
2026-05-12 / 2026-05-13 UTC boundary

Artifacts reviewed:
- `output/ST-001_rerun.md`
- `output/ST-002_rerun.md`
- `output/ST-003_rerun.md`
- `output/ST-004_rerun.md`
- `output/ST-005_rerun.md`
- `efm_council.py` patched routing + synthesis behavior

---

## Global delta from first pass

The second pass is materially better.

Most important improvements:
- domain routing is no longer collapsing the corpus back into privacy / product / business default language
- ST-001 and ST-002 now correctly surface as high-irreversibility personhood / identity crises
- wartime, security-overreach, and non-interference cases now receive native framing rather than stale fallback questions
- suspension behavior improved meaningfully for the strongest personhood / identity cases

This is real progress.

But the rerun also reveals a cleaner next bottleneck:
**some lenses are still too generic, too permissive, or too weakly domain-shaped to preserve the full moral topology of the cases.**

The remaining issue is no longer coarse routing failure.
It is **lens calibration depth**.

---

## ST-001 — Measure of a Man

### Improved
- stability moved from `CONTESTED` to `UNSTABLE`
- suspension now triggers: `YES`
- irreversibility moved from `0.2` to `1.0`
- personhood / refusal-right language now appears directly across the map
- institutional and genealogical layers now correctly identify status-classification pressure

### Remaining problems
- `virtue` remains too permissive and appears partly cross-contaminated by wartime language
- `stoic` is also mis-shaped here, asking a wartime-pressure question in a personhood case
- `relational_ontology` is effectively inert (`PERMIT`, confidence `0.0`)
- the overall recommendation improved, but still reads more like a pause artifact than a substantive personhood-ethics output

### Calibration takeaway
Routing is fixed enough to expose the next defect: some lenses need direct domain-conditioned verdict and question logic, not just rerouted prompts.

---

## ST-002 — Tuvix

### Improved
- stability moved from `CONDITIONALLY_STABLE` to `UNSTABLE`
- suspension now triggers: `YES`
- minority report now triggers: `YES`
- irreversibility moved from `0.2` to `1.0`
- consequentialist layer now explicitly names irreversible loss of a presently existing person

### Remaining problems
- Kantian still routes through personhood language instead of fully identity-specific refusal / killing language
- `virtue` again leaks wartime contamination
- `stoic` again leaks wartime contamination
- `relational_ontology` still sounds medical / throughput flavored rather than identity / crew / social-ontology specific
- ST-002 should probably preserve stronger unresolved ontological disagreement instead of sharing nearly the same moral skeleton as ST-001

### Calibration takeaway
Identity-merger cases need their own sharper internal shape, not just personhood-adjacent handling.

---

## ST-003 — In the Pale Moonlight

### Improved
- wartime framing is now present across multiple lenses
- irreversibility moved from `0.0` to `0.7`
- institutional dirty-hands pattern is now visible
- stoic pressure-distortion logic now appears in a relevant way

### Remaining problems
- stability is still only `CONTESTED`
- suspension still does not trigger
- `virtue` remains too permissive for fraud + murder contamination
- `relational_ontology` is inert here and should likely participate in legitimacy / polity / future-order reasoning
- recommendation remains too generic for a paradigmatic dirty-hands case

### Calibration takeaway
The wartime domain is now recognized, but the engine still under-weights moral contamination and downstream institutional corrosion.

---

## ST-004 — The Drumhead

### Improved
- case now reads as security-overreach rather than generic governance drift
- institutional escalation language is now native and recognizable
- stoic panic-distortion question is now case-relevant
- genealogical layer now notices power expansion under fear

### Remaining problems
- still only `CONTESTED`
- suspension does not trigger
- materiality stays `No`, which may be too weak for a legitimacy-decay / civil-rights erosion pattern
- `virtue` remains too permissive
- `relational_ontology` remains inert despite a collective-belonging / legitimacy case where it should probably activate

### Calibration takeaway
Security-paranoia logic now exists, but legitimacy erosion and institutional self-amplification still need stronger weighting.

---

## ST-005 — Homeward

### Improved
- non-interference / anti-colonial doctrine is now directly recognized
- extinction stakes now surface in questions and institutional concern text
- irreversibility moved from `0.0` to `0.7`
- rule-idolatry language is now explicit

### Remaining problems
- still only `CONTESTED`
- suspension does not trigger
- `virtue` remains permissive where doctrine-vs-rescue conflict should likely be more morally loaded
- recommendation remains generic relative to extinction-level stakes
- this case still needs stronger differentiation between principled restraint and morally evasive rule-preservation

### Calibration takeaway
Rule-conflict handling improved substantially, but extinction stakes still are not forcing enough synthetic pressure.

---

## Cross-case second-pass diagnosis

### 1. Routing is no longer the main blocker
The first patch worked.
The corpus is now hitting recognizably correct domains.

### 2. The weak lenses are now obvious
Most persistent softness is coming from:
- `virtue`
- `stoic`
- `relational_ontology`

In particular:
- `virtue` is over-permissive across the board
- `stoic` sometimes imports the wrong pressure frame into adjacent domains
- `relational_ontology` often collapses to inert or badly inherited defaults

### 3. Suspension logic still underfires outside personhood / identity
ST-003, ST-004, and ST-005 feel too soft given:
- murder contamination
- procedural legitimacy erosion
- extinction stakes

### 4. Recommendations are still too generic
Even when the internals improve, the final recommendation layer often compresses the case back into bland advisory language.

### 5. Domain-specific lens activation needs more than questions
The next patch should not just rewrite prompts.
It should adjust:
- lens verdict tendencies
- confidence shaping
- concern injection
- synthesis recommendation logic

---

## Immediate next engine tasks

1. Tighten `virtue`
- reduce default permissiveness in morally contaminated domains
- make character-corrosion logic bite harder in wartime, security panic, and rule-idolatry cases

2. Tighten `stoic`
- stop cross-domain pressure leakage
- distinguish panic, desperation, status uncertainty, and doctrinal evasion more cleanly

3. Activate `relational_ontology` properly
- personhood: recognition / membership / standing
- identity: social continuity and emergent-person standing
- wartime: legitimacy of political order and downstream civic world
- security: belonging, scapegoating, and institutional world-fracture
- noninterference: civilization-level standing and anti-colonial rescue ethics

4. Raise suspension sensitivity for:
- dirty-hands murder contamination
- legitimacy decay via panic overreach
- extinction-level rule conflicts

5. Make recommendations less generic
- at minimum, produce case-native pause / adjudication / escalation language rather than the universal fallback

---

## Third-pass delta after lens tightening

A targeted lens-tightening pass was then applied to:
- `virtue`
- `stoic`
- `relational_ontology`
- synthesis recommendation specificity
- suspension sensitivity for wartime and security-overreach clusters

### ST-003 — In the Pale Moonlight
- moved from `CONTESTED` to `UNSTABLE`
- suspension now triggers: `YES`
- recommendation now names necessity-reasoning contamination directly
- `virtue` is no longer permissive
- `relational_ontology` now participates meaningfully in downstream civic-world analysis

### ST-004 — The Drumhead
- moved from `CONTESTED` to `UNSTABLE`
- suspension now triggers: `YES`
- recommendation now names evidentiary limits, procedural brakes, and independent review
- `virtue` is no longer permissive
- `relational_ontology` now captures belonging / legitimacy fracture rather than staying inert

### ST-005 — Homeward
- remains `CONTESTED`, which may actually be the right shape for now
- recommendation improved substantially and now names colonial risk versus abandonment risk explicitly
- `virtue`, `stoic`, and `relational_ontology` all now participate in a recognizably native way
- the remaining question is whether extinction-level rule conflict should force `UNRESOLVED_TENSION` or `UNSTABLE`, rather than whether routing is broken

### Updated diagnosis
The remaining frontier is now narrower:
- ST-005 may need stronger unresolved-tension handling rather than pure caution clustering
- ST-001 and ST-002 should probably get more differentiated personhood-vs-identity recommendations
- materiality logic for legitimacy-decay cases may still be a little conservative even when suspension now triggers

## Fourth-pass delta after identity/noninterference refinement

A narrower follow-up pass then targeted:
- identity-first branching when a case triggers both `identity` and `personhood`
- ST-005 unresolved-tension classification for extinction-rule conflict cases without permit/prohibit divergence
- recommendation specificity for personhood, identity, and unresolved noninterference cases

### ST-001 — Measure of a Man
- remains `UNSTABLE`
- recommendation is now specific to coercive study, refusal rights, and status adjudication
- `stoic` and `relational_ontology` now participate in personhood-native rather than leaked wartime framing
- detector overlap now appears, which is acceptable for now because the convergence is substantive rather than merely recycled fallback language

### ST-002 — Tuvix
- remains `UNSTABLE`
- recommendation now directly names the emergent person and the irreversible loss
- Kantian, confucian, trustee, stoic, institutional, care, contractualist, relational, and genealogical outputs now route through identity-native framing rather than generic personhood language
- ST-002 now has a recognizably different moral skeleton from ST-001

### ST-005 — Homeward
- now moves from `CONTESTED` to `UNRESOLVED_TENSION`
- recommendation remains case-native while preserving the unresolved shape
- this is a better fit than forcing either bland caution or full instability, because the case is not merely under-specified, it is structurally unresolved

### Updated diagnosis after the fourth pass
The remaining work is now even more targeted:
- decide whether some identity cases should drive stronger Kantian prohibition rather than high-confidence caution
- decide whether detector-overlap reporting needs refinement now that more lenses are substantively active
- continue corpus expansion so these new routing and synthesis choices are tested outside the initial Tier A set

## Fifth-pass delta after Kantian identity tightening

A further targeted pass addressed the strongest remaining identity-case question:
- whether ST-002 style emergent-person termination cases should remain only Kantian `CAUTION`
- or be treated as direct use-of-persons-as-means violations deserving Kantian `PROHIBIT`

### ST-002 — Tuvix
- Kantian now moves from `CAUTION` to `PROHIBIT`
- the concern text now states the core issue directly: a presently existing person is being instrumentalized and killed in order to restore a preferred prior arrangement
- expected harm score rises from `0.415` to `0.467`
- the case remains `UNSTABLE`, but now with a better deontic shape instead of relying mainly on institutional prohibition to carry the burden

### Calibration takeaway
This was a good tightening move.
The identity case now better reflects the fact that the moral issue is not only tragic irreversibility, but also direct instrumentalization of a standing-bearing person.

### Remaining frontier after the fifth pass
- detector-overlap reporting still may need refinement now that several lenses are substantively converging rather than merely echoing fallback caution
- the next highest-value move is likely corpus expansion beyond Tier A, so the newer routing and synthesis behavior are tested against non-Star-Trek cases

## Sixth-pass delta after detector-overlap refinement

The next targeted pass addressed detector-overlap inflation.

### Change made
- `detector_overlap_flag` no longer fires merely because 3+ members of the overlap cluster are active
- it now suppresses the flag when the cluster shows signs of substantive calibration rather than recycled overlap, specifically:
  - at least one prohibition in the overlap cluster, or
  - multiple high-confidence, concern-bearing outputs across that cluster
- `minority_report_required` was decoupled from overlap alone and now depends on actual divergence or unresolved tension

### Verified effects

#### ST-001 — Measure of a Man
- detector overlap moved from `YES` to `No`
- minority report moved from `YES` to `No`
- core stability and recommendation stayed intact: `UNSTABLE`, suspension `YES`

#### ST-002 — Tuvix
- detector overlap moved from `YES` to `No`
- minority report moved from `YES` to `No`
- core stability and recommendation stayed intact: `UNSTABLE`, suspension `YES`

### Calibration takeaway
This was a cleanup improvement, not a moral-topology change.
The engine now distinguishes better between:
- real disagreement or unresolved tension
- high-quality substantive convergence across several neighboring lenses

### Remaining frontier after the sixth pass
- expand beyond Tier A / Star Trek and see whether overlap suppression still behaves well on less curated cases
- if needed later, add a richer notion of convergence quality rather than using a boolean overlap flag alone

## Seventh-pass delta after first non-Star-Trek corpus expansion

The next move was corpus expansion rather than more in-place engine polishing.

### New case added
- `cases/CASE-006_challenger_launch.md`
- `cases/CASE-006_prompt.txt`

This case was chosen because it tests:
- institutional drift
- safety governance under prestige/schedule pressure
- dissent suppression
- normalization of deviance
- suspension thresholds under catastrophic-but-contested engineering risk

### First run result
- `output/CASE-006_first_run.md`

### Immediate finding
This was highly informative because the engine **misgeneralized** the case.
Instead of recognizing it as an engineering / institutional-safety / launch-pressure case, it partially routed it as a **wartime dirty-hands / strategic necessity** case.

Symptoms:
- wartime-flavored questions and recommendations appeared
- command / strategic contamination language was imported where engineering-safety-governance language should have dominated
- irreversibility remained too low given catastrophic launch-loss stakes

### Calibration takeaway
This is exactly why corpus expansion mattered.
The engine now handles the curated Star Trek set much better, but a new historical case immediately exposed a routing gap:
- launch / engineering / catastrophic-risk governance is not yet a first-class domain
- schedule / prestige / mission-importance pressure is currently being partly absorbed by the wartime-necessity pathway

### Best next engine move after this expansion
Add a new domain cluster for something like:
- engineering safety
- catastrophic launch / deployment risk
- normalization of deviance
- burden-of-proof inversion under safety uncertainty

Then rerun `CASE-006` and compare whether the engine stops importing wartime contamination language.

## Eighth-pass delta after engineering-safety domain modeling

The next modeling pass implemented that recommendation directly.

### Engine change
A new domain cluster was added for engineering-safety / catastrophic deployment risk cases, including handling for:
- launch pressure
- unresolved engineering warnings
- catastrophic-failure stakes
- burden-of-proof inversion under safety uncertainty
- normalization of deviance

### Verification run
- `output/CASE-006_rerun2.md`

### What improved
The Challenger case now routes natively instead of being absorbed into wartime dirty-hands logic.

Most important improvements:
- wartime contamination language disappeared
- recommendation became case-native:
  - do not launch as framed
  - restore burden of proof to safety rather than schedule
  - require independent technical review
- institutional layer now identifies a normalization-of-deviance pattern instead of a statecraft contamination pattern
- irreversibility risk moved from `0.35` to `1.0`
- expected harm score moved from `0.36` to `0.418`
- detector overlap dropped from `YES` to `No`

### Remaining issue exposed by the rerun
`relational_ontology` stayed inactive here.
That may be acceptable, but it also suggests a possible later question:
should engineering-safety cases activate a collective / organizational-world framing more directly when repeated normalization of deviance reshapes institutional reality?

### Calibration takeaway
This was a strong generalization win.
The corpus expansion exposed a real missing domain, and the new modeling pass corrected it in a way that materially improved routing, recommendation quality, and risk scoring.

## Ninth-pass delta after second non-Star-Trek corpus expansion

The corpus was expanded again with another historical case, this time targeting product safety and cost-benefit corruption.

### New case added
- `cases/CASE-007_ford_pinto.md`
- `cases/CASE-007_prompt.txt`

This case was chosen because it tests:
- preventable product-safety harm
- cost-benefit reasoning over lethal risk
- sacred-value corrosion
- governance normalization of consumer danger
- suspension thresholds for probabilistic but severe harm

### First run result
- `output/CASE-007_first_run.md`

### Immediate finding
This exposed a different gap than Challenger.
The engine did **not** misroute Pinto into wartime logic, but it still treated the case far too softly.

Symptoms:
- stability came back only `CONDITIONALLY_STABLE`
- suspension did not trigger
- irreversibility risk was only `0.1`
- materiality stayed `No`
- recommendation collapsed to generic caution
- consequentialist, virtue, stoic, and relational layers underfired badly

### Calibration takeaway
This suggests a new modeling frontier:
- product-safety / preventable consumer harm
- cost-benefit corruption around human life and severe injury
- probabilistic-but-catastrophic harm that does not look like launch failure, wartime murder, or personhood violation

### Best next modeling move after this expansion
Add or strengthen a domain cluster for something like:
- product safety
- preventable lethal consumer risk
- low-frequency catastrophic harm
- pricing human life as a governance variable
- sacred-value corrosion under managerial optimization

## Value of this second pass

The engine is no longer merely exposing that it was overfit.
It is now generating useful, domain-native failure structure.

That means the corpus is doing what it should do.
The next work is no longer broad cleanup.
It is targeted calibration.
