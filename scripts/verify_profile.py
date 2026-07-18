#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATHS = {
    "fidelis-contracts": "packages/fidelis-contracts",
    "aconstellation": "packages/aconstellation",
    "trusted-runtime": "packages/trusted-runtime",
    "meaning-assay": "packages/meaning-assay",
    "ethics-council": "packages/ethics-council",
    "trustworthy-agent-stack": "packages/trustworthy-agent-stack",
    "attest-agent-conlang": "packages/attest-agent-conlang",
    "cer-telemetry": "packages/cer-telemetry",
    "sophron-cer": "packages/sophron-cer",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", choices=("minimal", "all-real"))
    args = parser.parse_args()

    profile = json.loads((ROOT / "profiles" / f"{args.profile}.json").read_text())
    failures: list[str] = []
    for component in profile["required_components"]:
        path = ROOT / PATHS[component]
        if not path.exists():
            failures.append(f"required component absent: {component} ({path.relative_to(ROOT)})")

    manifest = ROOT / "provenance" / "imported-sources.tsv"
    if profile["require_imported_source_manifest"] and not manifest.exists():
        failures.append("imported source revision manifest is required")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print(f"Profile {args.profile!r} has all required physical components.")
    print("Note: semantic adapter provenance and test status must be checked by runtime health/CI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
