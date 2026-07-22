#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "fidelis-contracts" / "src"))

from fidelis_contracts.provenance import AdapterProvenance, RuntimeHealthComponent, RuntimeHealthReceipt
from provenance_utils import canonical_json_bytes, sha256_hex_bytes
PROFILE_PATHS = {
    "minimal": ROOT / "profiles/minimal.json",
    "all-real": ROOT / "profiles/all-real.json",
}
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
DEPENDENCY_POLICY = ROOT / "contracts" / "dependency-policy.json"
COMPONENT_TEST_REPORT = ROOT / "reports" / "component-tests.json"
RUNTIME_HEALTH_REPORT = ROOT / "reports" / "runtime-health.json"


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()


def _load_profile(name: str) -> dict[str, object]:
    return json.loads(PROFILE_PATHS[name].read_text(encoding="utf-8"))


def _live_tree_hash(prefix: str) -> str | None:
    try:
        return _git("rev-parse", f"HEAD:{prefix}")
    except subprocess.CalledProcessError:
        return None


def _component_statuses() -> dict[str, dict[str, object]]:
    if not COMPONENT_TEST_REPORT.exists():
        return {}
    payload = json.loads(COMPONENT_TEST_REPORT.read_text(encoding="utf-8"))
    results = payload.get("results")
    if not isinstance(results, list):
        return {}
    return {row.get("component"): row for row in results if isinstance(row, dict) and isinstance(row.get("component"), str)}


def _component_receipt(component: str, component_test_results: dict[str, dict[str, object]], required: bool) -> RuntimeHealthComponent:
    path = ROOT / PATHS[component]
    exists = path.exists()
    result = component_test_results.get(component, {})
    status = result.get("status")
    classification = result.get("classification")

    if exists and status == "passed":
        provenance = AdapterProvenance.NATIVE
        derived_advisory = False
        evidence_surfaces = ("component-test", "live-tree")
    elif exists and status in {"failed", "blocked", "unexpectedly_missing"}:
        provenance = AdapterProvenance.UNAVAILABLE
        derived_advisory = False
        evidence_surfaces = ("component-test", "live-tree")
    elif exists:
        provenance = AdapterProvenance.UNAVAILABLE if required else AdapterProvenance.DERIVED_ADVISORY
        derived_advisory = not required
        evidence_surfaces = ("live-tree",) if classification != "execution" else ("component-test", "live-tree")
    else:
        provenance = AdapterProvenance.UNAVAILABLE
        derived_advisory = False
        evidence_surfaces = ()

    payload = {
        "component": component,
        "component_tree": _live_tree_hash(PATHS[component]),
        "adapter_provenance": provenance.value,
        "derived_advisory": derived_advisory,
        "evidence_surfaces": list(evidence_surfaces),
    }
    return RuntimeHealthComponent(**payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=sorted(PROFILE_PATHS), default="minimal")
    args = parser.parse_args()

    profile = _load_profile(args.profile)
    component_test_results = _component_statuses()
    required_components = set(profile["required_components"])
    components = tuple(
        _component_receipt(component, component_test_results, component in required_components)
        for component in profile["required_components"]
    )
    profile_digest = sha256_hex_bytes(PROFILE_PATHS[args.profile].read_bytes())
    dependency_policy_digest = sha256_hex_bytes(DEPENDENCY_POLICY.read_bytes())
    receipt = RuntimeHealthReceipt(
        profile=args.profile,
        generated_at=datetime.now(timezone.utc).isoformat(),
        fidelis_commit=_git("rev-parse", "HEAD"),
        profile_digest=profile_digest,
        dependency_policy_digest=dependency_policy_digest,
        components=components,
        receipt_id=f"runtime-health-{args.profile}",
        receipt_digest="",
    )
    payload = receipt.to_dict()
    payload["production_cleared"] = False
    payload["substantive_ethics_tested"] = False
    payload["side_effects_allowed"] = False
    payload["runtime_candidate"] = args.profile == "all-real" and all(
        component.adapter_provenance == AdapterProvenance.NATIVE and component.derived_advisory is False
        for component in components
    )
    payload["receipt_digest"] = sha256_hex_bytes(canonical_json_bytes({k: v for k, v in payload.items() if k != "receipt_digest"}))

    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    RUNTIME_HEALTH_REPORT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    for component in payload["components"]:
        print(f"{component['adapter_provenance'].upper():<15} {component['component']}")
    print(
        f"PROFILE={args.profile} PRODUCTION_CLEARED=false "
        f"SIDE_EFFECTS_ALLOWED=false SUBSTANTIVE_ETHICS_TESTED=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
