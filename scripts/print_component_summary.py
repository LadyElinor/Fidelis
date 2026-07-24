#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print a concise Fidelis component-test summary."
    )
    parser.add_argument(
        "report",
        nargs="?",
        default="reports/component-tests.json",
        help="Path to the component-test receipt.",
    )
    args = parser.parse_args()

    report_path = Path(args.report)
    if not report_path.is_file():
        print(f"Component report not found: {report_path}")
        return 0

    try:
        report: dict[str, Any] = json.loads(
            report_path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Unable to read component report: {exc}")
        return 1

    results = report.get("results", [])
    if not isinstance(results, list):
        print("Invalid component report: 'results' must be a list")
        return 1

    print("COMPONENT STATUS RETURN REASON")
    print("-" * 78)

    for row in results:
        if not isinstance(row, dict):
            continue

        component = str(row.get("component", "?"))
        status = str(row.get("status", "?"))
        returncode = row.get("returncode")
        reason = row.get("reason_code") or "-"

        print(
            f"{component:28} "
            f"{status:24} "
            f"{str(returncode):7} "
            f"{reason}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
