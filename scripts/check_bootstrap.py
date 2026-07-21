#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _plan_payload() -> dict[str, object]:
    completed = subprocess.run(
        ["bash", "-lc", "./scripts/sync_components.sh plan-json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.stderr.strip() or completed.stdout.strip() or "sync_components.sh plan-json failed")
    return json.loads(completed.stdout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args()

    payload = _plan_payload()
    components = payload.get("components")
    if not isinstance(components, list):
        print("FAIL: bootstrap plan payload has invalid components list")
        return 1

    failures: list[str] = []
    ready_components = 0
    for row in components:
        if not isinstance(row, dict):
            failures.append("bootstrap plan contains non-object component entry")
            continue
        name = str(row.get("name", "<unknown>"))
        action = row.get("action")
        path_state = row.get("path_state")
        receipt_state = row.get("receipt_state")
        row_failures: list[str] = []
        if action != "pull":
            row_failures.append(f"{name}: action is {action!r}, expected 'pull' after import materialization")
        if path_state != "present":
            row_failures.append(f"{name}: path_state is {path_state!r}, expected 'present'")
        if receipt_state != "present":
            row_failures.append(f"{name}: receipt_state is {receipt_state!r}, expected 'present'")
        if row_failures:
            failures.extend(row_failures)
        else:
            ready_components += 1

    summary = {
        "schema_version": "1.0",
        "mode": "bootstrap-check-summary",
        "total_components": len(components),
        "ready_components": ready_components,
        "failing_components": len(components) - ready_components,
        "failure_count": len(failures),
        "complete": not failures,
    }

    if args.summary_json:
        print(json.dumps(summary, indent=2))
        return 0 if not failures else 1

    print(
        f"Bootstrap status: ready={summary['ready_components']}/{summary['total_components']} "
        f"failing_components={summary['failing_components']} failure_count={summary['failure_count']}"
    )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print(f"Bootstrap materialization complete: {len(components)} components present with receipts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
