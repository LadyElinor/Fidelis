from __future__ import annotations

import sys
from pathlib import Path

from trusted_runtime.examples_runtime import run_golden_scenario
from trusted_runtime.review import run_review_input


USAGE = "Usage: trusted-runtime golden | trusted-runtime review-pr --input <path> [--output <dir>]"


def _value_after(flag: str, argv: list[str]) -> str | None:
    if flag not in argv:
        return None
    index = argv.index(flag)
    if index + 1 >= len(argv):
        return None
    return argv[index + 1]


def main() -> None:
    argv = sys.argv[1:]
    if not argv:
        print(USAGE)
        return

    if argv[0] == "golden":
        output_dir = Path.cwd()
        run_golden_scenario(output_dir)
        print("Artifacts written: decision_output.json and decision_report.md")
        return

    if argv[0] == "review-pr":
        input_arg = _value_after("--input", argv)
        if input_arg is None:
            print(USAGE)
            raise SystemExit(2)
        output_arg = _value_after("--output", argv)
        output_dir = Path(output_arg) if output_arg is not None else Path.cwd()
        run_review_input(Path(input_arg), output_dir)
        print("Artifacts written: decision_output.json and decision_report.md")
        return

    print(USAGE)


if __name__ == "__main__":
    main()
