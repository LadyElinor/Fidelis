from __future__ import annotations

import json
import sys
from pathlib import Path

from trusted_runtime.benchmark import evaluate_benchmark_file
from trusted_runtime.examples_runtime import run_golden_scenario
from trusted_runtime.integration.status import adapter_status
from trusted_runtime.review import run_review_input
from trusted_runtime.smoke import LiveStackRequirementError, run_live_stack_smoke


USAGE = "Usage: trusted-runtime golden | trusted-runtime review-pr --input <path> [--output <dir>] | trusted-runtime benchmark --input <path> [--output <dir>] | trusted-runtime live-stack-smoke --input <path> [--output <dir>] [--require-all-real] | trusted-runtime health"


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

    if argv[0] == "benchmark":
        input_arg = _value_after("--input", argv)
        if input_arg is None:
            print(USAGE)
            raise SystemExit(2)
        output_arg = _value_after("--output", argv)
        output_dir = Path(output_arg) if output_arg is not None else Path.cwd()
        evaluate_benchmark_file(Path(input_arg), output_dir)
        print("Artifacts written: benchmark_case_results.json, benchmark_report.json, and benchmark_report.md")
        return

    if argv[0] == "verify-authority-digest":
        journal = _value_after("--journal", argv)
        at = _value_after("--at", argv)
        digest = _value_after("--digest", argv)
        if not (journal and at and digest):
            print("usage: trusted-runtime verify-authority-digest --journal PATH --at ISO8601 --digest HEX")
            raise SystemExit(2)
        from trusted_runtime.authority_store import replay_verify_digest

        verdict = replay_verify_digest(Path(journal), at, digest)
        print(json.dumps(verdict.model_dump(mode="json"), indent=2))
        # The rejecter: a receipt whose digest cannot be reproduced from the
        # journal fold at its own evaluated_at exits non-zero.
        raise SystemExit(0 if verdict.accept else 1)

    if argv[0] == "live-stack-smoke":
        input_arg = _value_after("--input", argv)
        if input_arg is None:
            print(USAGE)
            raise SystemExit(2)
        output_arg = _value_after("--output", argv)
        output_dir = Path(output_arg) if output_arg is not None else Path.cwd()
        require_all_real = "--require-all-real" in argv
        try:
            run_live_stack_smoke(Path(input_arg), output_dir, require_all_real=require_all_real)
        except LiveStackRequirementError as exc:
            print(str(exc))
            raise SystemExit(1)
        print("Artifacts written: live_stack_smoke.json, smoke_decision_output.json, and smoke_decision_report.md")
        return

    if argv[0] == "health":
        print(json.dumps(adapter_status(), indent=2))
        return

    print(USAGE)


if __name__ == "__main__":
    main()
