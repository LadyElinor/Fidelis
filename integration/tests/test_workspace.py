from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _write_verify_boundaries_fixture(repo: Path) -> None:
    (repo / "contracts").mkdir()
    (repo / "scripts").mkdir()
    (repo / "packages").mkdir()
    (repo / "contracts" / "dependency-policy.json").write_text(
        (ROOT / "contracts" / "dependency-policy.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (repo / "scripts" / "verify_boundaries.py").write_text(
        (ROOT / "scripts" / "verify_boundaries.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )


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
    assert "trusted-runtime" in components["meaning-assay"]["test_may_depend_on"]
    assert "trusted-runtime" in components["ethics-council"]["test_may_depend_on"]


def test_verify_boundaries_reports_declared_policy_scope(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_verify_boundaries_fixture(repo)

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_boundaries.py")],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "Declared dependency policy valid:" in completed.stdout


def test_verify_boundaries_allows_declared_python_import(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_verify_boundaries_fixture(repo)

    source = repo / "packages" / "trustworthy-agent-stack" / "src" / "trustworthy_agent_stack"
    target = repo / "packages" / "ethics-council" / "src" / "ethics_council"
    source.mkdir(parents=True)
    target.mkdir(parents=True)
    (source / "__init__.py").write_text("from ethics_council import policy\n", encoding="utf-8")
    (target / "__init__.py").write_text("policy = object()\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_boundaries.py")],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "Observed Python src imports are within declared dependency policy" in completed.stdout


def test_verify_boundaries_rejects_forbidden_python_import(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_verify_boundaries_fixture(repo)

    source = repo / "packages" / "meaning-assay" / "src" / "meaning_assay"
    target = repo / "packages" / "trusted-runtime" / "src" / "trusted_runtime"
    source.mkdir(parents=True)
    target.mkdir(parents=True)
    (source / "__init__.py").write_text("from trusted_runtime import policy\n", encoding="utf-8")
    (target / "__init__.py").write_text("policy = object()\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_boundaries.py")],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "observed forbidden Python import: meaning-assay -> trusted-runtime" in completed.stderr


def test_verify_boundaries_allows_explicit_test_only_import(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_verify_boundaries_fixture(repo)

    source = repo / "packages" / "meaning-assay" / "tests"
    target = repo / "packages" / "trusted-runtime" / "src" / "trusted_runtime"
    source.mkdir(parents=True)
    target.mkdir(parents=True)
    (source / "test_runtime_boundary.py").write_text("from trusted_runtime import policy\n", encoding="utf-8")
    (target / "__init__.py").write_text("policy = object()\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_boundaries.py")],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "Observed Python test imports are within explicit test policy" in completed.stdout


def test_verify_boundaries_rejects_forbidden_test_only_import(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_verify_boundaries_fixture(repo)

    source = repo / "packages" / "attest-agent-conlang" / "tests"
    target = repo / "packages" / "trusted-runtime" / "src" / "trusted_runtime"
    source.mkdir(parents=True)
    target.mkdir(parents=True)
    (source / "test_runtime_boundary.py").write_text("from trusted_runtime import policy\n", encoding="utf-8")
    (target / "__init__.py").write_text("policy = object()\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_boundaries.py")],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "observed forbidden Python test import: attest-agent-conlang -> trusted-runtime" in completed.stderr


def test_verify_boundaries_test_policy_is_driven_by_policy_file(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_verify_boundaries_fixture(repo)

    policy_path = repo / "contracts" / "dependency-policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy["components"]["meaning-assay"]["test_may_depend_on"] = []
    policy_path.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")

    source = repo / "packages" / "meaning-assay" / "tests"
    target = repo / "packages" / "trusted-runtime" / "src" / "trusted_runtime"
    source.mkdir(parents=True)
    target.mkdir(parents=True)
    (source / "test_runtime_boundary.py").write_text("from trusted_runtime import policy\n", encoding="utf-8")
    (target / "__init__.py").write_text("policy = object()\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_boundaries.py")],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "observed forbidden Python test import: meaning-assay -> trusted-runtime" in completed.stderr


def test_verify_boundaries_rejects_unknown_test_policy_target(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_verify_boundaries_fixture(repo)

    policy_path = repo / "contracts" / "dependency-policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy["components"]["meaning-assay"]["test_may_depend_on"] = ["not-a-component"]
    policy_path.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_boundaries.py")],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "references unknown test_may_depend_on target(s): not-a-component" in completed.stderr


def test_verify_boundaries_rejects_non_list_test_policy(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_verify_boundaries_fixture(repo)

    policy_path = repo / "contracts" / "dependency-policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy["components"]["meaning-assay"]["test_may_depend_on"] = "trusted-runtime"
    policy_path.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_boundaries.py")],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "component 'meaning-assay' has non-list test_may_depend_on" in completed.stderr


def test_verify_boundaries_rejects_unknown_production_policy_target(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_verify_boundaries_fixture(repo)

    policy_path = repo / "contracts" / "dependency-policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy["components"]["meaning-assay"]["may_depend_on"] = ["fidelis-contracts", "not-a-component"]
    policy_path.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_boundaries.py")],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "references unknown may_depend_on target(s): not-a-component" in completed.stderr


def test_verify_boundaries_rejects_non_list_production_policy(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_verify_boundaries_fixture(repo)

    policy_path = repo / "contracts" / "dependency-policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy["components"]["meaning-assay"]["may_depend_on"] = "fidelis-contracts"
    policy_path.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_boundaries.py")],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "component 'meaning-assay' has non-list may_depend_on" in completed.stderr


def test_verify_boundaries_rejects_duplicate_production_policy_entries(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_verify_boundaries_fixture(repo)

    policy_path = repo / "contracts" / "dependency-policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy["components"]["meaning-assay"]["may_depend_on"] = ["fidelis-contracts", "fidelis-contracts"]
    policy_path.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_boundaries.py")],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "component 'meaning-assay' has duplicate may_depend_on entries" in completed.stderr


def test_verify_boundaries_rejects_duplicate_test_policy_entries(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_verify_boundaries_fixture(repo)

    policy_path = repo / "contracts" / "dependency-policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy["components"]["meaning-assay"]["test_may_depend_on"] = ["trusted-runtime", "trusted-runtime"]
    policy_path.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_boundaries.py")],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "component 'meaning-assay' has duplicate test_may_depend_on entries" in completed.stderr


def test_verify_boundaries_allows_declared_js_ts_import(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_verify_boundaries_fixture(repo)

    source_dir = repo / "packages" / "sophron-cer"
    target_dir = repo / "packages" / "cer-telemetry"
    (source_dir / "src").mkdir(parents=True)
    (target_dir / "src").mkdir(parents=True)
    (source_dir / "package.json").write_text(json.dumps({"name": "@fidelis/sophron-cer"}) + "\n", encoding="utf-8")
    (target_dir / "package.json").write_text(json.dumps({"name": "@fidelis/cer-telemetry"}) + "\n", encoding="utf-8")
    (source_dir / "src" / "index.ts").write_text("import { thing } from '@fidelis/cer-telemetry';\n", encoding="utf-8")
    (target_dir / "src" / "index.ts").write_text("export const thing = 1;\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_boundaries.py")],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "Observed JS/TS src imports are within declared dependency policy" in completed.stdout


def test_verify_boundaries_rejects_forbidden_js_ts_import(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_verify_boundaries_fixture(repo)

    source_dir = repo / "packages" / "cer-telemetry"
    target_dir = repo / "packages" / "trusted-runtime"
    (source_dir / "src").mkdir(parents=True)
    (target_dir / "src").mkdir(parents=True)
    (source_dir / "package.json").write_text(json.dumps({"name": "@fidelis/cer-telemetry"}) + "\n", encoding="utf-8")
    (target_dir / "package.json").write_text(json.dumps({"name": "@fidelis/trusted-runtime"}) + "\n", encoding="utf-8")
    (source_dir / "src" / "index.ts").write_text("const rt = require('@fidelis/trusted-runtime');\n", encoding="utf-8")
    (target_dir / "src" / "index.ts").write_text("export const thing = 1;\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_boundaries.py")],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "observed forbidden JS/TS import: cer-telemetry -> trusted-runtime" in completed.stderr


def test_verify_boundaries_allows_explicit_js_ts_test_import(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_verify_boundaries_fixture(repo)

    source_dir = repo / "packages" / "meaning-assay"
    target_dir = repo / "packages" / "trusted-runtime"
    (source_dir / "tests").mkdir(parents=True)
    (target_dir / "src").mkdir(parents=True)
    (source_dir / "package.json").write_text(json.dumps({"name": "@fidelis/meaning-assay"}) + "\n", encoding="utf-8")
    (target_dir / "package.json").write_text(json.dumps({"name": "@fidelis/trusted-runtime"}) + "\n", encoding="utf-8")
    (source_dir / "tests" / "runtime.test.ts").write_text("import { gate } from '@fidelis/trusted-runtime';\n", encoding="utf-8")
    (target_dir / "src" / "index.ts").write_text("export const gate = 1;\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_boundaries.py")],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "Observed JS/TS test imports are within explicit test policy" in completed.stdout


def test_verify_boundaries_rejects_forbidden_js_ts_test_import(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_verify_boundaries_fixture(repo)

    source_dir = repo / "packages" / "attest-agent-conlang"
    target_dir = repo / "packages" / "trusted-runtime"
    (source_dir / "tests").mkdir(parents=True)
    (target_dir / "src").mkdir(parents=True)
    (source_dir / "package.json").write_text(json.dumps({"name": "@fidelis/attest-agent-conlang"}) + "\n", encoding="utf-8")
    (target_dir / "package.json").write_text(json.dumps({"name": "@fidelis/trusted-runtime"}) + "\n", encoding="utf-8")
    (source_dir / "tests" / "runtime.test.ts").write_text("import { gate } from '@fidelis/trusted-runtime';\n", encoding="utf-8")
    (target_dir / "src" / "index.ts").write_text("export const gate = 1;\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_boundaries.py")],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "observed forbidden JS/TS test import: attest-agent-conlang -> trusted-runtime" in completed.stderr


def test_verify_boundaries_allows_declared_package_json_dependency(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_verify_boundaries_fixture(repo)

    source_dir = repo / "packages" / "sophron-cer"
    target_dir = repo / "packages" / "cer-telemetry"
    source_dir.mkdir(parents=True)
    target_dir.mkdir(parents=True)
    (source_dir / "package.json").write_text(
        json.dumps({"name": "@fidelis/sophron-cer", "dependencies": {"@fidelis/cer-telemetry": "^1.0.0"}}) + "\n",
        encoding="utf-8",
    )
    (target_dir / "package.json").write_text(json.dumps({"name": "@fidelis/cer-telemetry"}) + "\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_boundaries.py")],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "Observed package.json dependencies are within declared dependency policy" in completed.stdout


def test_verify_boundaries_rejects_forbidden_package_json_dependency(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_verify_boundaries_fixture(repo)

    source_dir = repo / "packages" / "cer-telemetry"
    target_dir = repo / "packages" / "trusted-runtime"
    source_dir.mkdir(parents=True)
    target_dir.mkdir(parents=True)
    (source_dir / "package.json").write_text(
        json.dumps({"name": "@fidelis/cer-telemetry", "dependencies": {"@fidelis/trusted-runtime": "^1.0.0"}}) + "\n",
        encoding="utf-8",
    )
    (target_dir / "package.json").write_text(json.dumps({"name": "@fidelis/trusted-runtime"}) + "\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_boundaries.py")],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "observed forbidden package.json dependency: cer-telemetry -> trusted-runtime" in completed.stderr
