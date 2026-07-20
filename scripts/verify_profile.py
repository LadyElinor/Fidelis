#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
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
MANIFEST_COLUMNS = ("name", "prefix", "branch", "commit", "url", "imported_at_utc")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SOURCE_REPOSITORIES = ROOT / "provenance" / "source-repositories.json"


def _load_manifest(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    failures: list[str] = []
    if not path.exists():
        return [], ["imported source revision manifest is required"]

    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != MANIFEST_COLUMNS:
            failures.append("imported source revision manifest has invalid header")
            return [], failures
        rows = [dict(row) for row in reader]

    if not rows:
        failures.append("imported source revision manifest is empty")
    for idx, row in enumerate(rows, start=2):
        if any(not row.get(column) for column in MANIFEST_COLUMNS):
            failures.append(f"imported source revision manifest row {idx} is incomplete")
            continue
        if not COMMIT_RE.fullmatch(row["commit"]):
            failures.append(f"imported source revision manifest row {idx} has invalid commit hash")
        if not row["url"].startswith("https://github.com/"):
            failures.append(f"imported source revision manifest row {idx} has non-GitHub source URL")
    return rows, failures


def _load_source_registry() -> dict[str, dict[str, str]]:
    data = json.loads(SOURCE_REPOSITORIES.read_text(encoding="utf-8"))
    return {
        source["slug"]: {
            "name": source["name"],
            "prefix": source["prefix"],
            "branch": source["branch"],
            "url": source["url"],
        }
        for source in data["sources"]
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

    if profile["require_imported_source_manifest"]:
        manifest_rows, manifest_failures = _load_manifest(ROOT / "provenance" / "imported-sources.tsv")
        failures.extend(manifest_failures)
        registry = _load_source_registry()
        manifest_by_prefix = {row["prefix"]: row for row in manifest_rows}
        imported_names = {row["name"] for row in manifest_rows}
        required_imported = [component for component in profile["required_components"] if component != "fidelis-contracts"]

        for component in required_imported:
            expected = registry.get(component)
            expected_prefix = PATHS[component]
            if expected is None:
                failures.append(f"required component missing from canonical source registry: {component}")
                continue
            row = manifest_by_prefix.get(expected_prefix)
            if row is None:
                failures.append(f"required component missing from imported source manifest: {component} ({expected_prefix})")
                continue
            if row["name"] != expected["name"]:
                failures.append(f"imported source manifest name mismatch for {component}: expected {expected['name']!r}, got {row['name']!r}")
            if row["branch"] != expected["branch"]:
                failures.append(f"imported source manifest branch mismatch for {component}: expected {expected['branch']!r}, got {row['branch']!r}")
            if row["url"] != expected["url"]:
                failures.append(f"imported source manifest URL mismatch for {component}: expected {expected['url']!r}, got {row['url']!r}")

        expected_prefixes = {registry[component]["prefix"] for component in required_imported if component in registry}
        extra_prefixes = sorted(prefix for prefix in manifest_by_prefix if prefix not in expected_prefixes)
        for prefix in extra_prefixes:
            failures.append(f"unexpected imported source manifest entry: {prefix}")

        if "Fidelis" in imported_names:
            failures.append("imported source revision manifest must not treat the destination repo as an imported component")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print(f"Profile {args.profile!r} has all required physical components and manifest receipts.")
    print("Note: semantic adapter provenance and test status must still be checked by runtime health/CI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
