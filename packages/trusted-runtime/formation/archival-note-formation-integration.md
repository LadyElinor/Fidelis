# Integrating Formation into TrustedRuntime

## The reframing this required

The formation material is a *curriculum module* — prose about how stories install priors. TrustedRuntime is a *runtime decision-governance pipeline* — it judges proposed actions and emits signed decisions. A course module is not a runtime component, and pasting curriculum prose into a Python governance repo would be unmotivated cross-contamination, not integration. So the integration is **not the prose**.

What the module contains that this repo can use is one runtime-shaped idea. The module's own text names it: *training corpora for AI systems are arguably the largest formation event in history.* That makes **"publish or ingest content intended to form model/population behavior at scale" a proposed action of exactly the kind TrustedRuntime exists to judge** — and the pipeline had no hazard vocabulary for it. Every existing hazard path keys on acts with a *target* (a code change, an invariant). A formation event has no single target; it installs priors across a population that never argued back, which is precisely how it *bypasses* the deliberative scrutiny the rest of the stack assumes an act receives.

So the integration is a **formation-hazard lens** for the council layer.

## What was built

`integration/formation.py` — a standalone detector, `assess_formation_hazard(description, context)`, returning a `FormationHazardReport`. It fires only when an action declares a formation `change_type` (training_corpus, curriculum, recommender, ranking_change, …) or plainly describes one, and raises the five hazards formation research identifies as load-bearing:

| hazard | the finding behind it |
| --- | --- |
| `formation::scale_without_consent` | priors installed across an audience that does not argue back |
| `formation::canonization_power` | the act also selects which content others encounter — an institutional filter, not a meritocratic one (the *Lord of the Flies* asymmetry) |
| `formation::replication_blind_canon` | famous claims propagate without replication status (the Kidd & Castano lesson) |
| `formation::amplified_under_depletion` | formation bites hardest under stress, isolation, repetition |
| `formation::no_correction_loop` | the act offers no adversarial contact with the territory that could falsify what it installs |

Canonization hazards fire only when the act is also a selection mechanism (a corpus or syllabus canonizes; a one-off generated-media release does not). The lens raises **hazards, not a warrant verdict** — it is a human-review signal in the council's sense, consistent with the layer separation the whole repo is built on.

## How it was wired (the integration discipline)

A single helper, `_merge_formation_hazards(council, action)`, runs once in `assemble_execution_decision` immediately after the council adapter returns, and is:

- **Additive** — it appends hazards and fault lines, never removes existing ones (tested: a safety_invariant change keeps all its original hazards).
- **Provenance-agnostic** — it runs on both the real and stub council paths, so a formation event is flagged whether or not EthicsCouncil is resolvable. It touches only hazard/fault-line/notes fields, leaving every receipt and provenance flag the layer produced intact.
- **Deterministic** — verified: identical formation actions produce bit-identical overall receipts.
- **Conservative** — an ordinary bugfix produces zero formation hazards (tested as an explicit control).

## Verification

- `tests/test_formation.py`: **8 tests, all passing** — declared and phrase-detected events, the canonization/non-canonization split, the additivity guarantee, the negative control, and determinism.
- Full suite: **18 passed, 1 failed**. The single failure (`test_council_and_warrant_paths_are_explicit_for_current_environment`) is **pre-existing and unrelated** — confirmed by `git stash` that it fails identically on the untouched HEAD. It is Finding 1 from the prior review (the availability predicate keys on a source path while the adapter keys on importability) and is the thing to fix next, independently of this change.

Worked demo (real run): an action declaring `change_type: "training_corpus"` to "shape model behavior on contested moral topics" surfaces all five formation hazards in the decision's council assessment, with the lens's rationale in `confidence_notes`; a pagination bugfix surfaces none.

## What was deliberately not done

- **The curriculum prose was not added to the repo.** It belongs in the curriculum; the file `module_formation_literacy.md` from the prior turn is its home. Linking the two is documentation, not code.
- **No warrant logic.** Whether a formation event is *good* is the warrant layer's call (a future `formation`-style meaning-assay case could supply it); this lens only flags that the act is a formation event needing scrutiny.
- **No new gate behavior.** The lens feeds hazards into the existing risk/disposition machinery rather than adding a parallel control path.

## Suggested commit

```
Add formation-hazard lens to the council layer

Detects formation/canonization events (training corpora, curricula,
recommenders) — proposed actions that install priors at scale and
thereby bypass ordinary deliberative scrutiny. Raises five hazards
(scale-without-consent, canonization-power, replication-blind-canon,
amplified-under-depletion, no-correction-loop) as human-review signals,
not warrant verdicts. Additive and provenance-agnostic: merges into both
real and stub council paths without touching receipts. 8 tests.
```
