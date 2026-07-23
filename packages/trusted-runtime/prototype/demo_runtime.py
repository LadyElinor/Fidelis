from __future__ import annotations

import sys
from pathlib import Path

from runtime.orchestrator import run_case


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python demo_runtime.py <path-to-case-json>")
        return 1

    try:
        summary = run_case(argv[1])
    except Exception as exc:
        print(f"Runtime error: {exc}")
        return 1

    print(f"Decision: {summary['runtime_decision']}")
    if 'risk_state' in summary:
        print(f"Risk: {summary['risk_state']}")
    print(f"Integrity: {summary['decision_integrity']}")
    print(f"Reason: {summary['reason']}")

    dissent = summary.get("unresolved_dissent", [])
    print(f"Dissent: {', '.join(dissent) if dissent else 'none'}")
    print(f"Receipt: {summary['receipt_hash']}")
    print(f"Artifacts: {Path(summary['artifacts_dir'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
