from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.provenance_utils import sha256_hex_bytes

ROOT = Path(__file__).resolve().parents[2]


def _write_component_test_fixture(repo: Path) -> None:
    (repo / "profiles").mkdir()
    (repo / "scripts").mkdir()
    (repo / "packages").mkdir()
    (repo / "reports").mkdir()
    (repo / "contracts").mkdir()
    (repo / "packages" / "fidelis-contracts" / "src" / "fidelis_contracts").mkdir(parents=True)
    (repo / "scripts" / "run_component_tests.py").write_text(
        (ROOT / "scripts" / "run_component_tests.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (repo / "scripts" / "run_runtime_health.py").write_text(
        (ROOT / "scripts" / "run_runtime_health.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (repo / "scripts" / "provenance_utils.py").write_text(
        (ROOT / "scripts" / "provenance_utils.py").read_text(encoding="utf-8"),
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
    (repo / "contracts" / "dependency-policy.json").write_text(
        (ROOT / "contracts" / "dependency-policy.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (repo / "packages" / "fidelis-contracts" / "src" / "fidelis_contracts" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "packages" / "fidelis-contracts" / "src" / "fidelis_contracts" / "provenance.py").write_text(
        (ROOT / "packages" / "fidelis-contracts" / "src" / "fidelis_contracts" / "provenance.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    contracts = repo / "packages" / "fidelis-contracts"
    (contracts / "test_smoke.py").write_text("def test_smoke():\n    assert True\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "-c", "user.name=Test User", "-c", "user.email=test@example.com", "commit", "-m", "fixture"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


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
    assert "PROFILE=minimal PRODUCTION_CLEARED=false SIDE_EFFECTS_ALLOWED=false SUBSTANTIVE_ETHICS_TESTED=false" in completed.stdout
    payload = json.loads((repo / "reports" / "component-tests.json").read_text(encoding="utf-8"))
    assert payload["profile"] == "minimal"
    assert payload["production_cleared"] is False
    assert payload["side_effects_allowed"] is False
    assert payload["substantive_ethics_tested"] is False
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
    assert "PROFILE=all-real PRODUCTION_CLEARED=false SIDE_EFFECTS_ALLOWED=false SUBSTANTIVE_ETHICS_TESTED=true" in completed.stdout
    payload = json.loads((repo / "reports" / "component-tests.json").read_text(encoding="utf-8"))
    assert payload["profile"] == "all-real"
    assert payload["production_cleared"] is False
    assert payload["side_effects_allowed"] is False
    assert payload["substantive_ethics_tested"] is True
    results = {row["component"]: row for row in payload["results"]}
    assert results["aconstellation"]["status"] == "unexpectedly_missing"


def test_run_runtime_health_minimal_emits_bound_receipt_fields(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_component_test_fixture(repo)

    env = {**__import__("os").environ, "PYTHONPATH": str(repo / "packages" / "fidelis-contracts" / "src")}
    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "run_component_tests.py"), "--profile", "minimal"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert completed.returncode == 0

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "run_runtime_health.py"), "--profile", "minimal"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert completed.returncode == 0
    assert "PROFILE=minimal PRODUCTION_CLEARED=false SIDE_EFFECTS_ALLOWED=false SUBSTANTIVE_ETHICS_TESTED=false" in completed.stdout
    payload = json.loads((repo / "reports" / "runtime-health.json").read_text(encoding="utf-8"))
    assert payload["profile"] == "minimal"
    assert payload["production_cleared"] is False
    assert payload["side_effects_allowed"] is False
    assert payload["substantive_ethics_tested"] is False
    assert payload["fidelis_commit"] == subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    assert payload["profile_digest"] == sha256_hex_bytes((repo / "profiles" / "minimal.json").read_bytes())
    assert payload["dependency_policy_digest"] == sha256_hex_bytes((repo / "contracts" / "dependency-policy.json").read_bytes())
    results = {row["component"]: row for row in payload["components"]}
    assert results["fidelis-contracts"]["adapter_provenance"] == "native"
    assert results["fidelis-contracts"]["component_tree"] == subprocess.check_output(
        ["git", "rev-parse", "HEAD:packages/fidelis-contracts"], cwd=repo, text=True
    ).strip()


def test_run_runtime_health_all_real_marks_missing_required_components_unavailable(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_component_test_fixture(repo)

    env = {**__import__("os").environ, "PYTHONPATH": str(repo / "packages" / "fidelis-contracts" / "src")}
    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "run_component_tests.py"), "--profile", "all-real"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert completed.returncode == 1

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "run_runtime_health.py"), "--profile", "all-real"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert completed.returncode == 0
    assert "PROFILE=all-real PRODUCTION_CLEARED=false SIDE_EFFECTS_ALLOWED=false SUBSTANTIVE_ETHICS_TESTED=true" in completed.stdout

    payload = json.loads((repo / "reports" / "runtime-health.json").read_text(encoding="utf-8"))
    assert payload["production_cleared"] is False
    assert payload["side_effects_allowed"] is False
    assert payload["substantive_ethics_tested"] is True
    results = {row["component"]: row for row in payload["components"]}
    assert results["fidelis-contracts"]["adapter_provenance"] == "native"
    assert results["aconstellation"]["adapter_provenance"] == "unavailable"
    assert results["aconstellation"]["derived_advisory"] is False
    assert results["aconstellation"]["component_tree"] is None
