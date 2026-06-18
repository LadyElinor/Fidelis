#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RECEIPT_PATH = REPO_ROOT / "outputs" / "alignment_eval" / "alignment_eval_receipt_v0_1.json"
VOLATILE_KEYS = {"generated_at", "timestamp", "timestamps", "export_timestamp", "started_at", "created_at"}


def strip_volatile(value):
    if isinstance(value, dict):
        return {k: strip_volatile(v) for k, v in sorted(value.items()) if k not in VOLATILE_KEYS}
    if isinstance(value, list):
        return [strip_volatile(v) for v in value]
    return value


def run_eval() -> dict:
    subprocess.run(["node", "examples/alignment_eval/run_alignment_eval.js"], cwd=REPO_ROOT, check=True)
    return json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))


def main() -> int:
    first = strip_volatile(run_eval())
    second = strip_volatile(run_eval())
    if first != second:
        print("::error::alignment eval receipt differs across identical runs after stripping volatile fields")
        print(json.dumps({"first": first, "second": second}, indent=2))
        return 1
    print("alignment eval determinism: normalized receipt stable across two runs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
