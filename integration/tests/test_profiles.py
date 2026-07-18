from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_minimal_profile_is_seed_runnable() -> None:
    profile = json.loads((ROOT / "profiles/minimal.json").read_text())
    assert profile["required_components"] == ["fidelis-contracts"]
    assert (ROOT / "packages/fidelis-contracts").exists()


def test_all_real_profile_forbids_stubs_and_derived_advisory() -> None:
    profile = json.loads((ROOT / "profiles/all-real.json").read_text())
    assert profile["allow_stubbed_adapters"] is False
    assert profile["allow_derived_advisory"] is False
    assert profile["require_imported_source_manifest"] is True
    assert "aconstellation" in profile["required_components"]
