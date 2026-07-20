#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from provenance_utils import canonical_json_bytes, manifest_rows, sha256_hex_bytes

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
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
TREE_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
SOURCE_REPOSITORIES = ROOT / "provenance" / "source-repositories.json"
COMPONENT_TEST_REPORT = ROOT / "reports" / "component-tests.json"
IMPORT_RECEIPTS = ROOT / "provenance" / "import-receipts"


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _load_manifest(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    failures: list[str] = []
    if not path.exists():
        return [], ["imported source revision manifest is required"]
    try:
        rows = manifest_rows(path)
    except ValueError as exc:
        return [], [str(exc)]

    if not rows:
        failures.append("imported source revision manifest is empty")
    for idx, row in enumerate(rows, start=2):
        if not COMMIT_RE.fullmatch(row["commit"]):
            failures.append(f"imported source revision manifest row {idx} has invalid commit hash")
        if not TREE_RE.fullmatch(row["tree"]):
            failures.append(f"imported source revision manifest row {idx} has invalid tree hash")
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


def _live_tree_hash(prefix: str) -> str | None:
    try:
        tree = _git("rev-parse", f"HEAD:{prefix}")
    except subprocess.CalledProcessError:
        return None
    return tree if TREE_RE.fullmatch(tree) else None


def _component_remote_name(name: str) -> str:
    remote = "source-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return remote


def _upstream_reachability_status(name: str, branch: str, commit: str) -> tuple[str, str | None]:
    override_path = ROOT / "provenance" / "test-reachability-overrides.json"
    if override_path.exists():
        overrides = json.loads(override_path.read_text(encoding="utf-8"))
        key = f"{name}|{branch}|{commit}"
        if key in overrides:
            status = overrides[key]
            if status == "reachable":
                return "reachable", None
            if status == "unavailable":
                return "unavailable", f"upstream reachability evidence unavailable for {name}: override marked unavailable"
            if status == "invalid":
                return "invalid", f"upstream commit not present locally for {name}: {commit}"
            if status == "unreachable":
                return "unreachable", f"upstream commit not reachable from declared branch for {name}: {commit} not ancestor of declared branch"

    remote = _component_remote_name(name)
    try:
        _git("show-ref", "--verify", f"refs/remotes/{remote}/{branch}")
    except subprocess.CalledProcessError:
        return "unavailable", f"upstream reachability evidence unavailable for {name}: missing local ref refs/remotes/{remote}/{branch}"

    try:
        _git("cat-file", "-e", f"{commit}^{{commit}}")
    except subprocess.CalledProcessError:
        return "invalid", f"upstream commit not present locally for {name}: {commit}"

    try:
        _git("merge-base", "--is-ancestor", commit, f"refs/remotes/{remote}/{branch}")
    except subprocess.CalledProcessError:
        return "unreachable", f"upstream commit not reachable from declared branch for {name}: {commit} not ancestor of {remote}/{branch}"
    return "reachable", None


def _receipt_name(prefix: str) -> str:
    return prefix.replace("/", "--") + ".json"


def _validate_import_receipt(component: str, row: dict[str, str]) -> list[str]:
    failures: list[str] = []
    path = IMPORT_RECEIPTS / _receipt_name(row["prefix"])
    if not path.exists():
        return [f"import receipt missing for required component: {component} ({path.relative_to(ROOT)})"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    digest = payload.get("receipt_digest")
    if not isinstance(digest, str) or not DIGEST_RE.fullmatch(digest):
        failures.append(f"import receipt has invalid digest field for {component}")
    canonical_payload = dict(payload)
    canonical_payload.pop("receipt_digest", None)
    actual_digest = sha256_hex_bytes(canonical_json_bytes(canonical_payload))
    if digest != actual_digest:
        failures.append(f"import receipt digest mismatch for {component}")
    if payload.get("component") != component:
        failures.append(f"import receipt component mismatch for {component}")
    if payload.get("prefix") != row["prefix"]:
        failures.append(f"import receipt prefix mismatch for {component}")
    if payload.get("upstream_commit") != row["commit"]:
        failures.append(f"import receipt commit mismatch for {component}")
    if payload.get("imported_tree") != row["tree"]:
        failures.append(f"import receipt tree mismatch for {component}")
    if payload.get("upstream_url") != row["url"]:
        failures.append(f"import receipt URL mismatch for {component}")
    previous_digest = payload.get("previous_receipt_digest")
    if previous_digest is not None and not DIGEST_RE.fullmatch(previous_digest):
        failures.append(f"import receipt previous digest is invalid for {component}")
    row_digest = payload.get("manifest_row_digest")
    expected_row_digest = sha256_hex_bytes(canonical_json_bytes(row))
    if row_digest != expected_row_digest:
        failures.append(f"import receipt manifest row digest mismatch for {component}")
    return failures


def _load_component_test_report(required_components: list[str]) -> list[str]:
    failures: list[str] = []
    if not COMPONENT_TEST_REPORT.exists():
        return ["component test receipt is required for all-real profile"]
    payload = json.loads(COMPONENT_TEST_REPORT.read_text(encoding="utf-8"))
    if payload.get("profile") != "all-real":
        failures.append("component test receipt must be generated with profile 'all-real'")
    results = payload.get("results")
    if not isinstance(results, list):
        failures.append("component test receipt has invalid results payload")
        return failures
    results_by_component = {row.get("component"): row for row in results if isinstance(row, dict)}
    for component in required_components:
        row = results_by_component.get(component)
        if row is None:
            failures.append(f"component test receipt missing required component: {component}")
            continue
        status = row.get("status")
        if status != "passed":
            failures.append(f"component test receipt requires passed status for {component}, got {status!r}")
    return failures


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
            reachability_status, reachability_failure = _upstream_reachability_status(row["name"], row["branch"], row["commit"])
            if reachability_status != "reachable" and reachability_failure:
                failures.append(reachability_failure)
            live_tree = _live_tree_hash(expected_prefix)
            if live_tree is None:
                failures.append(f"unable to resolve live tree hash for required component: {component} ({expected_prefix})")
            elif row["tree"] != live_tree:
                failures.append(f"imported source manifest tree mismatch for {component}: expected live tree {live_tree!r}, got {row['tree']!r}")
            failures.extend(_validate_import_receipt(component, row))

        expected_prefixes = {registry[component]["prefix"] for component in required_imported if component in registry}
        extra_prefixes = sorted(prefix for prefix in manifest_by_prefix if prefix not in expected_prefixes)
        for prefix in extra_prefixes:
            failures.append(f"unexpected imported source manifest entry: {prefix}")

        if "Fidelis" in imported_names:
            failures.append("imported source revision manifest must not treat the destination repo as an imported component")

    if args.profile == "all-real":
        failures.extend(_load_component_test_report(profile["required_components"]))
        if profile.get("allow_stubbed_adapters") is False:
            failures.append("semantic adapter provenance must still be checked by runtime health receipts before all-real can pass")
        if profile.get("allow_derived_advisory") is False:
            failures.append("derived advisory status must still be checked by runtime health receipts before all-real can pass")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    if args.profile == "all-real":
        print(f"Profile {args.profile!r} has all required physical components, manifest receipts, and component test receipts.")
    else:
        print(f"Profile {args.profile!r} has all required physical components.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
