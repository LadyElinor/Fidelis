# Ethics Council Lite

A small, shareable ethical diagnostics program inspired by the Ethical Field Method and EFAS-style failure analysis.

This version is intentionally lightweight:
- no API keys
- no external model SDKs
- no FastAPI
- no dependency-heavy setup
- pure Python standard library

It does **not** pretend to solve ethics or produce final moral truth. It produces a structured, multi-lens hazard map for a decision prompt under uncertainty.

## What it does

Given a decision, it runs several evaluative lenses:
- Kantian constraint
- Consequentialist outcomes
- Virtue trajectory
- Confucian role obligations
- Trustee stewardship
- Stoic reality alignment
- Institutional red flags
- Care ethics
- Contractualist rejectability
- Relational / deep-time standing
- Genealogical adversarial critique

Then it synthesizes:
- convergences
- fault lines
- suspension triggers
- minority-report conditions
- unresolved questions
- risk instrumentation

## Design stance

This project treats ethics primarily as **failure detection under uncertainty**, not as a machine for manufacturing consensus.

Core commitments:
- preserve adversarial independence across lenses
- treat uncertainty as first-class, not residual
- distinguish hazard detection from verdict generation
- allow unresolved ethical tension to persist
- prefer suspension over false decisiveness in contested high-risk cases

## Usage

```bash
python cli.py "Should we deploy this system before the safety audit is complete?"
```

From file:

```bash
python cli.py --file decision.txt
```

Save JSON and Markdown outputs:

```bash
python cli.py "Your decision" --output output/my_decision
```

## Design

This is a deterministic local scaffold, not an LLM product. Each lens uses rule-guided promptless heuristics and question generation so the system is:
- runnable anywhere Python runs
- easy to inspect
- easy to extend
- safe to publish as a starting point

Recent architecture improvements:
- added irreversibility risk as a first-class signal
- added detector-overlap instrumentation to reduce synthetic confidence
- constrained synthesis so disagreement and overlap can force contested outputs
- surfaced minority-report conditions in reporting

## Files

- `cli.py` — command line entry point
- `efm_council.py` — core evaluation engine
- `report.py` — markdown formatter
- `sample_decision.txt` — example input

## Important caveat

This is still a heuristic prototype. It is best understood as a transparent ethical auditing scaffold, not as an authoritative decision-maker.

Known next-step priorities:
- formalize detector independence more rigorously
- build a stress-test corpus of canonical cases
- calibrate null baselines for disagreement and overlap
- refine synthesis constraints further for irreversible high-stakes domains

## Next steps

Natural extensions:
- replace heuristic lenses with pluggable model backends
- add richer scoring rules
- add YAML-configurable lenses
- add a web UI or API wrapper

## License

MIT
