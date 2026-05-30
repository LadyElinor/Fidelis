#!/usr/bin/env python3
"""Run the full minimal proof and validate the produced export."""

from __future__ import annotations

import sys
import tempfile

try:
    from .demo import run_demo
    from .sophron_ingest import validate_cer_export
except ImportError:  # pragma: no cover
    from demo import run_demo
    from sophron_ingest import validate_cer_export


def main() -> int:
    print("Running TrustworthyAgentStack Integration Validation...\n")
    with tempfile.TemporaryDirectory() as tmpdir:
        export_path = run_demo(output_dir=tmpdir)
        if not export_path:
            print("Demo failed to produce export.")
            return 1

        result = validate_cer_export(export_path)
        if result["valid"]:
            print("\nINTEGRATION VALIDATION PASSED")
            print("The loop EthicsCouncil -> CER -> SOPHRON validation works.")
            return 0

        print("\nINTEGRATION VALIDATION FAILED")
        for violation in result["violations"]:
            print(f" - {violation}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
