from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _init_repo(repo: Path) -> None:
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True, text=True)


def test_sync_components_plan_succeeds_under_git_bash_with_autocrlf_enabled(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)

    for relative in [
        ".gitattributes",
        "scripts/sync_components.sh",
        "scripts/provenance_utils.py",
        "provenance/source-repositories.json",
    ]:
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((ROOT / relative).read_text(encoding="utf-8"), encoding="utf-8", newline="\n")

    (repo / "scripts" / "sync_components.sh").chmod(0o755)
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "fixture"], cwd=repo, check=True, capture_output=True, text=True)

    env = {**os.environ, "HOME": os.environ.get("HOME", str(repo))}
    completed = subprocess.run(
        ["bash", "-lc", "./scripts/sync_components.sh plan-json"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert completed.returncode == 0
    assert '"mode": "plan-json"' in completed.stdout
