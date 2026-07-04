"""gaplog: record what an agent said vs. what an independent check found.

One record per completion claim. Six fields. Nothing else.
"""
import datetime
import json
import os

__version__ = "0.1.0"

FIELDS = ("ts", "task_id", "reported", "verified", "match", "verifier")


class GapLog:
    """Append-only JSONL journal of (self-reported, independently verified) pairs.

    `verifier` is a short human-readable description of the independent
    verification path (e.g. "git-remote-head via read-only deploy key").
    Independence is not proven by this tool; it is asserted here so it
    can be inspected and challenged.
    """

    def __init__(self, path):
        self.path = str(path)

    def record(self, task_id, reported, verified, verifier):
        rec = {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "task_id": str(task_id),
            "reported": str(reported),
            "verified": str(verified),
            "match": str(reported) == str(verified),
            "verifier": str(verifier),
        }
        line = json.dumps(rec, sort_keys=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())
        return rec


def read(path):
    """Yield records from a gaplog JSONL file. Malformed lines raise."""
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if line:
                rec = json.loads(line)
                missing = [k for k in FIELDS if k not in rec]
                if missing:
                    raise ValueError(f"line {n}: missing fields {missing}")
                yield rec
