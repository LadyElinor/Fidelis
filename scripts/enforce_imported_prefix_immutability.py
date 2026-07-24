#!/usr/bin/env python
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "provenance" / "imported-sources.tsv"
RECEIPT_DIR = ROOT / "provenance" / "import-receipts"
SYNC_SCRIPT = "scripts/sync_components.sh"


def run_git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def changed_files(base_ref: str, head_ref: str) -> list[str]:
    out = run_git(["diff", "--name-only", f"{base_ref}..{head_ref}"])
    return [line.strip() for line in out.splitlines() if line.strip()]


def imported_prefixes() -> list[str]:
    with MANIFEST.open(encoding="utf-8", newline="") as fh:
        return [row["prefix"] for row in csv.DictReader(fh, delimiter="\t")]


def main() -> int:
    base_ref = sys.argv[1] if len(sys.argv) > 1 else "HEAD~1"
    head_ref = sys.argv[2] if len(sys.argv) > 2 else "HEAD"

    files = changed_files(base_ref, head_ref)
    prefixes = imported_prefixes()
    prefix_hits = [path for path in files if any(path == prefix or path.startswith(prefix + "/") for prefix in prefixes)]
    if not prefix_hits:
        print("Imported-prefix immutability check: no imported-prefix edits detected.")
        return 0

    manifest_changed = "provenance/imported-sources.tsv" in files
    receipt_changed = any(path.startswith("provenance/import-receipts/") and path.endswith(".json") for path in files)
    sync_script_changed = SYNC_SCRIPT in files

    if manifest_changed and receipt_changed:
        print("Imported-prefix immutability check: imported-prefix edits detected with regenerated manifest and receipts.")
        print("Review required: ensure the change arrived via the controlled subtree import/pull flow.")
        return 0

    print("ERROR: direct edits beneath imported component prefixes are not allowed without provenance regeneration.", file=sys.stderr)
    print("Changed imported-prefix paths:", file=sys.stderr)
    for path in prefix_hits:
        print(f"  - {path}", file=sys.stderr)
    print(file=sys.stderr)
    print("Expected reconciliation path:", file=sys.stderr)
    print(f"  1. run {SYNC_SCRIPT} plan", file=sys.stderr)
    print(f"  2. run {SYNC_SCRIPT} pull", file=sys.stderr)
    print("  3. commit regenerated provenance/imported-sources.tsv and provenance/import-receipts/*.json", file=sys.stderr)
    if sync_script_changed:
        print(file=sys.stderr)
        print("Note: scripts/sync_components.sh changed in this range; confirm the subtree flow was intentionally updated.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
