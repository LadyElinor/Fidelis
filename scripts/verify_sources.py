#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "provenance" / "source-repositories.json"


def main() -> int:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    failures: list[str] = []
    seen_names: set[str] = set()
    seen_prefixes: set[str] = set()

    for source in data["sources"]:
        name = source["name"]
        prefix = source["prefix"]
        if name in seen_names:
            failures.append(f"duplicate source name: {name}")
        if prefix in seen_prefixes:
            failures.append(f"duplicate source prefix: {prefix}")
        seen_names.add(name)
        seen_prefixes.add(prefix)

        path = ROOT / prefix
        if path.exists():
            if not any(path.iterdir()):
                failures.append(f"source path exists but is empty: {prefix}")
        else:
            print(f"PENDING  {name:<24} {prefix}")

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 1

    print(f"Source manifest valid: {len(seen_names)} components declared.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
