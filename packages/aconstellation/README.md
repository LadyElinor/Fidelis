# gaplog

Your agent said "done." Did the world agree?

Agents self-report completion. Sometimes the report describes local state that never reached the world — a "pushed" that wasn't, a "sent" that didn't, a "deployed" that isn't. gaplog is a passive logger that records both sides of that claim so you can measure how often they disagree in **your** stack, before deciding whether the gap is worth building around.

It records six fields per completion claim and nothing else:

```
ts, task_id, reported, verified, match, verifier
```

## Try it in 30 seconds

```
python demo/said_done.py
```

```
[task-001] agent reported: 'completed:pushed'   remote says: 'not-on-remote'   -> DISCREPANCY
[task-002] agent reported: 'completed:pushed'   remote says: 'completed:pushed' -> MATCH
```

Run 1 is an agent that commits, reports success, and never pushes. Run 2 actually pushes. A verifier that reads the remote directly — through a path the agent doesn't hold — settles it either way. Both outcomes land in `gaps.jsonl`.

## Drop it into your own loop

```python
from gaplog import GapLog

log = GapLog("gaps.jsonl")
reported = agent_self_report            # whatever your agent claimed
verified = check_world_state()          # your independent check
log.record(task_id, reported, verified,
           verifier="describe the independent path here")
```

The `verifier` field is a human-readable description of *how* the claim was independently checked. gaplog does not prove independence; it makes the asserted verification path inspectable so it can be challenged. Good verifiers share no credentials, process state, or toolchain with the agent being checked.

## Decide the threshold before you collect the data

```
python -m gaplog preregister prereg.json --min-n 500 --rate 0.01
# ... collect ...
python -m gaplog summarize gaps.jsonl --prereg prereg.json
```

Preregistration records, ahead of time, the sample size and discrepancy rate at which you'd judge independent verification worth adopting. `summarize` refuses to issue a verdict if the prereg file postdates the first record. The question this tool exists to answer — *how often do self-reports and verified state actually diverge?* — is only worth answering if the answer can come back "not often enough to matter."

## What this is not

Not a framework, not a runtime, not a policy layer. ~50 lines of stdlib Python that produce a receipt: what was claimed, what was found, when, and by what path. If the measured gap in your stack justifies more machinery, that machinery is a separate decision.
