# meaning-assay

A deterministic, receipts-first engine for reading an act through twenty-seven
traditions of meaning, and separating two questions the word "meaning" usually
hides:

- **significance** — does this act matter, and where does its weight come from?
- **warrant** — is the act good; should it have been done?

Most traditions answer only one of these. The framework's central, and
uncomfortable, result is that an act can be **maximal in significance and void
of warrant**. This package makes that split computable, auditable, and hard to
fudge.

## Why it exists

The design was not assumed; it was forced by two worked cases.

Read through the traditions, **Eva Mozes Kor's forgiveness** (a survivor of
Auschwitz forgiving, as self-emancipation that does not excuse the crime) sorted
the lenses by whether they could account for a free act performed against
everything that should have made it impossible. The agency-centred lenses won.

That looked like a discovery until the same procedure was run on its moral
inverse, the **Trinity** test. The agency lenses that crowned Kor crown
Oppenheimer just as firmly, because Trinity is also a free act at the limit. They
grip a catastrophe with the confidence they brought to a grace. So the ranking
had been measuring **agency, not goodness**. "A free act against impossibility"
is morally neutral.

Running the inverse also revealed a second axis. The lenses that *condemn* the
bomb are not the ones that passed the forgiveness test; they are the
teleological and relational ones, because each carries a standard of the good.
The agency lenses can only describe. Hence two axes, not one, and hence this
engine.

## The model

Each of the 27 traditions is tagged with the functions it can perform:

| function | meaning |
|---|---|
| `SIGNIFICANCE` | explains where an act gets its weight (agency, becoming, perception) |
| `WARRANT` | carries a standard by which the **act itself** can be judged good or bad |
| `MECHANISM` | describes a structural/formal property without locating significance or supplying a good |

A tradition with **no** functions is the null/critical position — exactly the
role of strict nihilism, which denies both a locus of significance and a
standard of the good.

The `WARRANT` tag uses a strict rule: a tradition earns it only if it can judge
the *act*, not merely the agent's inner state or an instrumental/epistemic goal.
That is why **Stoic** is significance-only here (its virtue standard is
agent-directed and went silent on the act at Trinity), and why **Scientific
Naturalist** and **Pragmatist** are mechanism, not warrant (their standards are
"does the model hold" and "does it work").

These tags are **analytical claims, not facts**. They live in `lenses.py` in the
open, each with a one-line rationale, so they can be argued with and revised. The
same goes for every per-case reading: each carries citations, and a reading
backed only by a summary is flagged `provisional` until a primary source confirms
it.

## What the engine does (and does not do)

The engine never invents a judgment. Given authored readings it computes only
structural products:

- **significance axis** `[0,1]`: engaged weight across meaning-domains (a
  momentous atrocity scores high; the moral charge is *not* here)
- **warrant axis** `[-1,1]`: grip-weighted average of the verdicts from the
  lenses that actually carry warrant
- **quadrant**: `LUMINOUS`, `CHARGED`, `DANGEROUS`, `QUIET_GOOD`, `INERT`,
  `CORROSIVE`
- **failure-mode trips**: the per-lens failure mode proved more discriminating
  than the thesis on catastrophic acts, so it is a first-class diagnostic
- **contrasting-pair deltas**: the honest unit of analysis is the pair, because
  a single case measures the case as much as the framework

It also enforces one integrity rule that makes the split mean something: **a lens
may return a moral verdict only if it carries warrant.** A significance-only or
mechanism lens that tries to judge the act raises `IntegrityError`.

Every analysis can emit a **receipt**: a SHA-256 over canonical inputs and
outputs, so the same inputs always produce the same manifest and any drift shows
up in a diff.

## Install

```bash
pip install -e .            # or: pip install -e ".[dev]" for the tests
```

## Use

```bash
meaning-assay lenses                 # list the 27 traditions and their functions
meaning-assay run kor                # analyze one case
meaning-assay run trinity
meaning-assay pair kor trinity       # the contrast: significance holds, warrant inverts
meaning-assay receipt trinity        # deterministic signed manifest
meaning-assay render kor --out kor.md
```

```python
from meaning_assay import analyze, compare
from meaning_assay.cases import get as get_case

print(analyze(get_case("trinity")).quadrant)         # DANGEROUS
print(compare(get_case("kor"), get_case("trinity")).finding)
# "significance holds, warrant inverts"
```

## Adding a case

A case is data: one `Reading` per tradition. Encode `grip` (how firmly the lens
engages), `polarity` (affirms / neutral / violates the lens's domain),
`failure_tripped`, a `verdict` (only for warrant lenses; `NA` otherwise), a short
prose note, and citations. See `src/meaning_assay/cases/kor.py` for the pattern.
`validate()` will refuse the case if a reading is missing or if a non-warrant
lens tries to judge.

## Layout

```
src/meaning_assay/
  model.py      value objects: Function, Grip, Polarity, Verdict, Tradition, Reading, Case
  lenses.py     the 27 traditions as data, with function tags + rationale
  engine.py     deterministic scoring + integrity checks
  pairs.py      contrasting-pair analysis
  receipts.py   canonical hashing and verification
  report.py     markdown rendering (regenerates the per-case essays)
  cases/        kor.py, trinity.py  (worked cases)
tests/          integrity, quadrants, the pair finding, receipt determinism
examples/       run_kor_vs_trinity.py
```

## Design principles

1. **Judgments are data, not code.** Every analytical claim is an editable,
   citable record.
2. **Significance is not warrant.** The two axes never collapse into one number.
3. **Only warrant lenses may judge.** Enforced, not merely intended.
4. **Failure modes are diagnostic.** They catch what theses miss on bad acts.
5. **The pair is the unit.** Single-case results are treated as suspect.
6. **Primary sources before trust.** Summary-only readings are flagged
   provisional.
7. **Determinism and receipts.** Same inputs, same manifest; tampering breaks
   verification.

## Status

`0.1.0`. The lensbook and the two cases are seeds. The function tags and verdicts
are offered precisely so they can be contested; a pull request that re-tags a
tradition with a better rationale is the intended use.
