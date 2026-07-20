from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

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
    (repo / "scripts" / "verify_profile.py").write_text(
        (ROOT / "scripts" / "verify_profile.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (repo / "scripts" / "provenance_utils.py").write_text(
        (ROOT / "scripts" / "provenance_utils.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (repo / "profiles" / "all-real.json").write_text(
        (ROOT / "profiles" / "all-real.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (repo / "provenance" / "source-repositories.json").write_text(
        (ROOT / "provenance" / "source-repositories.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    required = json.loads((ROOT / "profiles" / "all-real.json").read_text())["required_components"]
    for component in required:
        path = repo / PATH_MAP[component]
        path.mkdir(parents=True, exist_ok=True)
        (path / "placeholder.txt").write_text("x", encoding="utf-8")


def _write_valid_manifest_and_receipt(repo: Path, reachability_overrides: dict[str, str] | None = None) -> None:
    registry = json.loads((ROOT / "provenance" / "source-repositories.json").read_text())["sources"]
    rows = ["name\tprefix\tbranch\tcommit\ttree\turl\timported_at_utc"]
    (repo / "provenance" / "import-receipts").mkdir(parents=True, exist_ok=True)
    for source in registry:
        row = {
            "name": source["name"],
            "prefix": source["prefix"],
            "branch": source["branch"],
            "commit": "a" * 40,
            "tree": "b" * 40,
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
            "imported_tree": "b" * 40,
            "manifest_row_digest": "",
            "fidelis_commit": "c" * 40,
            "imported_at_utc": "2026-07-20T00:00:00Z",
            "previous_receipt_digest": None,
        }
        payload["manifest_row_digest"] = __import__("hashlib").sha256(
            json.dumps(row, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        payload["receipt_digest"] = __import__("hashlib").sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        receipt_name = source["prefix"].replace("/", "--") + ".json"
        (repo / "provenance" / "import-receipts" / receipt_name).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (repo / "provenance" / "imported-sources.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    payload = {
        "generated_at": "2026-07-20T00:00:00Z",
        "profile": "all-real",
        "required_components": json.loads((repo / "profiles" / "all-real.json").read_text())["required_components"],
        "results": [
            {
                "component": component,
                "command": ["pytest"],
                "status": "passed",
                "returncode": 0,
                "classification": "execution",
            }
            for component in json.loads((repo / "profiles" / "all-real.json").read_text())["required_components"]
        ],
    }
    (repo / "reports" / "component-tests.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if reachability_overrides is not None:
        (repo / "provenance" / "test-reachability-overrides.json").write_text(
            json.dumps(reachability_overrides, indent=2) + "\n",
            encoding="utf-8",
        )


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
    )

    assert completed.returncode == 1
    assert "upstream reachability evidence unavailable for TrustedRuntime" in completed.stdout
