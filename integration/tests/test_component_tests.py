from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _write_component_test_fixture(repo: Path) -> None:
    (repo / "profiles").mkdir()
    (repo / "scripts").mkdir()
    (repo / "packages").mkdir()
    (repo / "reports").mkdir()
    (repo / "scripts" / "run_component_tests.py").write_text(
        (ROOT / "scripts" / "run_component_tests.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (repo / "profiles" / "minimal.json").write_text(
        (ROOT / "profiles" / "minimal.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (repo / "profiles" / "all-real.json").write_text(
        (ROOT / "profiles" / "all-real.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    contracts = repo / "packages" / "fidelis-contracts"
    contracts.mkdir(parents=True)
    (contracts / "test_smoke.py").write_text("def test_smoke():\n    assert True\n", encoding="utf-8")


def test_run_component_tests_minimal_tolerates_absent_optional_components(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_component_test_fixture(repo)

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "run_component_tests.py"), "--profile", "minimal"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    payload = json.loads((repo / "reports" / "component-tests.json").read_text(encoding="utf-8"))
    assert payload["profile"] == "minimal"
    results = {row["component"]: row for row in payload["results"]}
    assert results["aconstellation"]["status"] == "expected_not_applicable"


def test_run_component_tests_all_real_fails_when_required_components_are_absent(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_component_test_fixture(repo)

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "run_component_tests.py"), "--profile", "all-real"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    payload = json.loads((repo / "reports" / "component-tests.json").read_text(encoding="utf-8"))
    assert payload["profile"] == "all-real"
    results = {row["component"]: row for row in payload["results"]}
    assert results["aconstellation"]["status"] == "unexpectedly_missing"
