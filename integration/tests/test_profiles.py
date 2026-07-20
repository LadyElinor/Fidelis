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
    (repo / "scripts" / "verify_profile.py").write_text(
        (ROOT / "scripts" / "verify_profile.py").read_text(encoding="utf-8"),
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
        (repo / PATH_MAP[component]).mkdir(parents=True, exist_ok=True)
        (repo / PATH_MAP[component] / "placeholder.txt").write_text("x", encoding="utf-8")


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
        "name\tprefix\tbranch\tcommit\turl\timported_at_utc\n"
        "bogus\tpackages/bogus\tmain\t123\thttps://github.com/example/bogus\t2026-07-18T00:00:00Z\n",
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

    rows = ["name\tprefix\tbranch\tcommit\turl\timported_at_utc"]
    registry = json.loads((ROOT / "provenance" / "source-repositories.json").read_text())["sources"]
    for source in registry:
        branch = "wrong-branch" if source["slug"] == "meaning-assay" else source["branch"]
        rows.append(
            f"{source['name']}\t{source['prefix']}\t{branch}\t{'a'*40}\t{source['url']}\t2026-07-18T00:00:00Z"
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

    rows = ["name\tprefix\tbranch\tcommit\turl\timported_at_utc"]
    registry = json.loads((ROOT / "provenance" / "source-repositories.json").read_text())["sources"]
    for source in registry:
        if source["slug"] == "trusted-runtime":
            continue
        rows.append(
            f"{source['name']}\t{source['prefix']}\t{source['branch']}\t{'b'*40}\t{source['url']}\t2026-07-18T00:00:00Z"
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
