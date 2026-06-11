from __future__ import annotations

import sys
from pathlib import Path

from trusted_runtime.examples_runtime import run_golden_scenario


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "golden":
        output_dir = Path.cwd()
        run_golden_scenario(output_dir)
        print("Artifacts written: decision_output.json and decision_report.md")
        return

    print("Usage: trusted-runtime golden")


if __name__ == "__main__":
    main()
