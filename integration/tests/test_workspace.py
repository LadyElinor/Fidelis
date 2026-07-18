from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_source_prefixes_are_unique_and_under_packages() -> None:
    data = json.loads((ROOT / "provenance/source-repositories.json").read_text())
    prefixes = [source["prefix"] for source in data["sources"]]
    assert len(prefixes) == len(set(prefixes))
    assert all(prefix.startswith("packages/") for prefix in prefixes)


def test_dependency_policy_contains_all_declared_components() -> None:
    sources = json.loads((ROOT / "provenance/source-repositories.json").read_text())
    policy = json.loads((ROOT / "contracts/dependency-policy.json").read_text())
    declared = {source["slug"] for source in sources["sources"]}
    governed = set(policy["components"])
    assert declared <= governed
    assert "fidelis-contracts" in governed
    assert "aconstellation" in declared


def test_assessor_packages_do_not_depend_on_runtime_policy() -> None:
    policy = json.loads((ROOT / "contracts/dependency-policy.json").read_text())
    components = policy["components"]
    assert "trusted-runtime" not in components["meaning-assay"]["may_depend_on"]
    assert "trusted-runtime" not in components["ethics-council"]["may_depend_on"]
