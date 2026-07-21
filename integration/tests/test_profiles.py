from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from scripts.provenance_utils import canonical_json_bytes, sha256_hex_bytes

ROOT = Path(__file__).resolve().parents[2]


PATH_MAP = {
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


def _write_profile_fixture_repo(repo: Path) -> None:
    (repo / "profiles").mkdir()
    (repo / "provenance").mkdir()
    (repo / "scripts").mkdir()
    (repo / "packages").mkdir()
    (repo / "reports").mkdir()
    (repo / "contracts").mkdir()
    (repo / "packages" / "fidelis-contracts" / "src" / "fidelis_contracts").mkdir(parents=True, exist_ok=True)
    (repo / "scripts" / "verify_profile.py").write_text(
        (ROOT / "scripts" / "verify_profile.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (repo / "scripts" / "provenance_utils.py").write_text(
        (ROOT / "scripts" / "provenance_utils.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    component_test_script = (ROOT / "scripts" / "run_component_tests.py").read_text(encoding="utf-8")
    component_test_script = component_test_script.replace('["npm", "test"]', '[sys.executable, "-c", "print(\'ok\')"]')
    (repo / "scripts" / "run_component_tests.py").write_text(
        component_test_script,
        encoding="utf-8",
    )
    (repo / "scripts" / "run_runtime_health.py").write_text(
        (ROOT / "scripts" / "run_runtime_health.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (repo / "profiles" / "all-real.json").write_text(
        (ROOT / "profiles" / "all-real.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (repo / "profiles" / "minimal.json").write_text(
        (ROOT / "profiles" / "minimal.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (repo / "provenance" / "source-repositories.json").write_text(
        (ROOT / "provenance" / "source-repositories.json").read_text(encoding="utf-8"),
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

    required = json.loads((ROOT / "profiles" / "all-real.json").read_text())["required_components"]
    for component in required:
        path = repo / PATH_MAP[component]
        path.mkdir(parents=True, exist_ok=True)
        if component in {"cer-telemetry", "sophron-cer"}:
            (path / "placeholder.txt").write_text("x", encoding="utf-8")
        elif component == "trustworthy-agent-stack":
            (path / "tests").mkdir(parents=True, exist_ok=True)
            (path / "tests" / "test_smoke.py").write_text("def test_smoke():\n    assert True\n", encoding="utf-8")
        else:
            (path / "test_smoke.py").write_text("def test_smoke():\n    assert True\n", encoding="utf-8")

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "-c", "user.name=Test User", "-c", "user.email=test@example.com", "commit", "-m", "fixture"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


def _write_valid_manifest_and_receipt(repo: Path, reachability_overrides: dict[str, str] | None = None) -> None:
    registry = json.loads((ROOT / "provenance" / "source-repositories.json").read_text())["sources"]
    rows = ["name\tprefix\tbranch\tcommit\ttree\turl\timported_at_utc"]
    (repo / "provenance" / "import-receipts").mkdir(parents=True, exist_ok=True)
    fidelis_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    for source in registry:
        tree = subprocess.check_output(["git", "rev-parse", f"HEAD:{source['prefix']}"], cwd=repo, text=True).strip()
        row = {
            "name": source["name"],
            "prefix": source["prefix"],
            "branch": source["branch"],
            "commit": "a" * 40,
            "tree": tree,
            "url": source["url"],
            "imported_at_utc": "2026-07-20T00:00:00Z",
        }
        rows.append(
            f"{row['name']}\t{row['prefix']}\t{row['branch']}\t{row['commit']}\t{row['tree']}\t{row['url']}\t{row['imported_at_utc']}"
        )
        payload = {
            "schema_version": "1.0",
            "receipt_type": "component-import",
            "component": source["slug"],
            "name": source["name"],
            "prefix": source["prefix"],
            "mode": "import",
            "upstream_url": source["url"],
            "upstream_branch": source["branch"],
            "upstream_commit": "a" * 40,
            "imported_tree": tree,
            "manifest_row_digest": "",
            "fidelis_commit": fidelis_commit,
            "imported_at_utc": "2026-07-20T00:00:00Z",
            "previous_receipt_digest": None,
        }
        payload["manifest_row_digest"] = sha256_hex_bytes(canonical_json_bytes(row))
        payload["receipt_digest"] = sha256_hex_bytes(canonical_json_bytes(payload))
        receipt_name = source["prefix"].replace("/", "--") + ".json"
        (repo / "provenance" / "import-receipts" / receipt_name).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (repo / "provenance" / "imported-sources.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    if reachability_overrides is not None:
        (repo / "provenance" / "test-reachability-overrides.json").write_text(
            json.dumps(reachability_overrides, indent=2) + "\n",
            encoding="utf-8",
        )

    env = {
        **os.environ,
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(repo / "packages" / "fidelis-contracts" / "src"),
    }
    if reachability_overrides is not None:
        env["FIDELIS_ALLOW_TEST_REACHABILITY_OVERRIDES"] = "1"

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "run_component_tests.py"), "--profile", "all-real"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    if completed.returncode != 0:
        raise AssertionError(f"fixture component test generation failed: {completed.stdout}\n{completed.stderr}")

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "run_runtime_health.py"), "--profile", "all-real"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    if completed.returncode != 0:
        raise AssertionError(f"fixture runtime health generation failed: {completed.stdout}\n{completed.stderr}")


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


def test_verify_profile_all_real_rejects_bogus_manifest(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_profile_fixture_repo(repo)

    (repo / "provenance" / "imported-sources.tsv").write_text(
        "name\tprefix\tbranch\tcommit\ttree\turl\timported_at_utc\n"
        "bogus\tpackages/bogus\tmain\t123\t456\thttps://github.com/example/bogus\t2026-07-18T00:00:00Z\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_profile.py"), "all-real"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "required component missing from imported source manifest" in completed.stdout or "invalid commit hash" in completed.stdout


def test_verify_profile_all_real_rejects_branch_mismatch(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_profile_fixture_repo(repo)

    rows = ["name\tprefix\tbranch\tcommit\ttree\turl\timported_at_utc"]
    registry = json.loads((ROOT / "provenance" / "source-repositories.json").read_text())["sources"]
    for source in registry:
        branch = "wrong-branch" if source["slug"] == "meaning-assay" else source["branch"]
        rows.append(
            f"{source['name']}\t{source['prefix']}\t{branch}\t{'a'*40}\t{'b'*40}\t{source['url']}\t2026-07-18T00:00:00Z"
        )
    (repo / "provenance" / "imported-sources.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_profile.py"), "all-real"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "imported source manifest branch mismatch for meaning-assay" in completed.stdout


def test_verify_profile_all_real_rejects_missing_required_manifest_entry(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_profile_fixture_repo(repo)

    rows = ["name\tprefix\tbranch\tcommit\ttree\turl\timported_at_utc"]
    registry = json.loads((ROOT / "provenance" / "source-repositories.json").read_text())["sources"]
    for source in registry:
        if source["slug"] == "trusted-runtime":
            continue
        rows.append(
            f"{source['name']}\t{source['prefix']}\t{source['branch']}\t{'b'*40}\t{'c'*40}\t{source['url']}\t2026-07-18T00:00:00Z"
        )
    (repo / "provenance" / "imported-sources.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_profile.py"), "all-real"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "required component missing from imported source manifest: trusted-runtime" in completed.stdout


def test_verify_profile_all_real_end_to_end_accepts_generated_artifacts(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_profile_fixture_repo(repo)
    _write_valid_manifest_and_receipt(
        repo,
        {
            "TrustedRuntime|main|aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa": {"status": "reachable", "tree": subprocess.check_output(["git", "rev-parse", "HEAD:packages/trusted-runtime"], cwd=repo, text=True).strip()},
            "AConstellation|main|aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa": {"status": "reachable", "tree": subprocess.check_output(["git", "rev-parse", "HEAD:packages/aconstellation"], cwd=repo, text=True).strip()},
            "AttestAgentConlang|main|aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa": {"status": "reachable", "tree": subprocess.check_output(["git", "rev-parse", "HEAD:packages/attest-agent-conlang"], cwd=repo, text=True).strip()},
            "meaning-assay|master|aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa": {"status": "reachable", "tree": subprocess.check_output(["git", "rev-parse", "HEAD:packages/meaning-assay"], cwd=repo, text=True).strip()},
            "SOPHRON-CER|main|aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa": {"status": "reachable", "tree": subprocess.check_output(["git", "rev-parse", "HEAD:packages/sophron-cer"], cwd=repo, text=True).strip()},
            "CER-Telemetry|main|aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa": {"status": "reachable", "tree": subprocess.check_output(["git", "rev-parse", "HEAD:packages/cer-telemetry"], cwd=repo, text=True).strip()},
            "TrustworthyAgentStack|main|aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa": {"status": "reachable", "tree": subprocess.check_output(["git", "rev-parse", "HEAD:packages/trustworthy-agent-stack"], cwd=repo, text=True).strip()},
            "EthicsCouncil|master|aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa": {"status": "reachable", "tree": subprocess.check_output(["git", "rev-parse", "HEAD:packages/ethics-council"], cwd=repo, text=True).strip()},
        },
    )

    env = {
        **os.environ,
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(repo / "packages" / "fidelis-contracts" / "src"),
        "FIDELIS_ALLOW_TEST_REACHABILITY_OVERRIDES": "1",
    }
    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "run_component_tests.py"), "--profile", "all-real"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert completed.returncode == 0

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "run_runtime_health.py"), "--profile", "all-real"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert completed.returncode == 0

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_profile.py"), "all-real"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert completed.returncode == 0
    assert "Profile 'all-real' has all required physical components" in completed.stdout


def test_verify_profile_all_real_requires_component_test_receipt(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_profile_fixture_repo(repo)
    _write_valid_manifest_and_receipt(repo)
    (repo / "reports" / "component-tests.json").unlink()

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_profile.py"), "all-real"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "component test receipt is required for all-real profile" in completed.stdout


def test_verify_profile_all_real_requires_runtime_health_receipt(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_profile_fixture_repo(repo)
    _write_valid_manifest_and_receipt(repo)
    (repo / "reports" / "runtime-health.json").unlink()

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_profile.py"), "all-real"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "runtime health receipt is required for all-real profile" in completed.stdout


def test_verify_profile_all_real_rejects_nonpassing_required_component(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_profile_fixture_repo(repo)
    _write_valid_manifest_and_receipt(repo)

    payload = json.loads((repo / "reports" / "component-tests.json").read_text(encoding="utf-8"))
    payload["results"][1]["status"] = "blocked"
    (repo / "reports" / "component-tests.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_profile.py"), "all-real"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "component test receipt requires passed status" in completed.stdout


def test_verify_profile_all_real_rejects_non_native_runtime_health(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_profile_fixture_repo(repo)
    _write_valid_manifest_and_receipt(repo)

    payload = json.loads((repo / "reports" / "runtime-health.json").read_text(encoding="utf-8"))
    payload["components"][1]["adapter_provenance"] = "stub"
    (repo / "reports" / "runtime-health.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_profile.py"), "all-real"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "runtime health requires native adapter provenance" in completed.stdout


def test_verify_profile_all_real_rejects_derived_runtime_health(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_profile_fixture_repo(repo)
    _write_valid_manifest_and_receipt(repo)

    payload = json.loads((repo / "reports" / "runtime-health.json").read_text(encoding="utf-8"))
    payload["components"][1]["derived_advisory"] = True
    (repo / "reports" / "runtime-health.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_profile.py"), "all-real"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "runtime health requires non-derived advisory status" in completed.stdout


def test_verify_profile_all_real_rejects_runtime_health_profile_digest_mismatch(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_profile_fixture_repo(repo)
    _write_valid_manifest_and_receipt(repo)

    payload = json.loads((repo / "reports" / "runtime-health.json").read_text(encoding="utf-8"))
    payload["profile_digest"] = "0" * 64
    (repo / "reports" / "runtime-health.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_profile.py"), "all-real"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "runtime health receipt profile digest mismatch" in completed.stdout


def test_verify_profile_all_real_rejects_runtime_health_dependency_policy_digest_mismatch(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_profile_fixture_repo(repo)
    _write_valid_manifest_and_receipt(repo)

    payload = json.loads((repo / "reports" / "runtime-health.json").read_text(encoding="utf-8"))
    payload["dependency_policy_digest"] = "1" * 64
    (repo / "reports" / "runtime-health.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_profile.py"), "all-real"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "runtime health receipt dependency policy digest mismatch" in completed.stdout


def test_verify_profile_all_real_requires_import_receipts(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_profile_fixture_repo(repo)
    _write_valid_manifest_and_receipt(repo)
    receipt = repo / "provenance" / "import-receipts" / "packages--trusted-runtime.json"
    receipt.unlink()

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_profile.py"), "all-real"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "import receipt missing for required component: trusted-runtime" in completed.stdout


def test_verify_profile_all_real_rejects_import_receipt_row_mismatch(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_profile_fixture_repo(repo)
    _write_valid_manifest_and_receipt(repo)
    receipt = repo / "provenance" / "import-receipts" / "packages--trusted-runtime.json"
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    payload["upstream_commit"] = "d" * 40
    receipt.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_profile.py"), "all-real"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "import receipt digest mismatch for trusted-runtime" in completed.stdout or "import receipt commit mismatch for trusted-runtime" in completed.stdout


def test_verify_profile_all_real_rejects_unreachable_upstream_commit(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_profile_fixture_repo(repo)
    _write_valid_manifest_and_receipt(
        repo,
        {
            "TrustedRuntime|main|aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa": "unreachable",
        },
    )

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_profile.py"), "all-real"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env={**__import__("os").environ, "FIDELIS_ALLOW_TEST_REACHABILITY_OVERRIDES": "1"},
    )

    assert completed.returncode == 1
    assert "upstream commit not reachable from declared branch for TrustedRuntime" in completed.stdout


def test_verify_profile_all_real_rejects_unavailable_upstream_evidence(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_profile_fixture_repo(repo)
    _write_valid_manifest_and_receipt(
        repo,
        {
            "TrustedRuntime|main|aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa": "unavailable",
        },
    )

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_profile.py"), "all-real"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env={**__import__("os").environ, "FIDELIS_ALLOW_TEST_REACHABILITY_OVERRIDES": "1"},
    )

    assert completed.returncode == 1
    assert "upstream reachability evidence unavailable for TrustedRuntime" in completed.stdout


def test_verify_profile_rejects_override_file_outside_test_mode(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_profile_fixture_repo(repo)
    _write_valid_manifest_and_receipt(
        repo,
        {
            "TrustedRuntime|main|aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa": "reachable",
        },
    )

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "verify_profile.py"), "all-real"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "test reachability override file must not be present outside test mode" in completed.stdout
