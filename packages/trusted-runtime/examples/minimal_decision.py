from __future__ import annotations

from pathlib import Path

from trusted_runtime.examples_runtime import run_golden_scenario


def main() -> None:
    run_golden_scenario(Path.cwd())
    print("Artifacts written: decision_output.json and decision_report.md")


if __name__ == "__main__":
    main()
