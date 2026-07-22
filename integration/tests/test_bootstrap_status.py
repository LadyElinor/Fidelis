from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_check_bootstrap_summary_json_emits_nonproduction_flags(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "scripts").mkdir()
    (repo / "scripts" / "check_bootstrap.py").write_text(
        (ROOT / "scripts" / "check_bootstrap.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (repo / "scripts" / "sync_components.sh").write_text(
        "#!/usr/bin/env bash\n"
        "cat <<'JSON'\n"
        "{\n"
        "  \"schema_version\": \"1.0\",\n"
        "  \"mode\": \"plan-json\",\n"
        "  \"components\": [\n"
        "    {\"name\": \"TrustedRuntime\", \"action\": \"import\", \"path_state\": \"missing\", \"receipt_state\": \"missing\"}\n"
        "  ]\n"
        "}\n"
        "JSON\n",
        encoding="utf-8",
        newline="\n",
    )
    (repo / "scripts" / "sync_components.sh").chmod(0o755)

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "check_bootstrap.py"), "--summary-json"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert payload["profile"] == "bootstrap-materialization"
    assert payload["production_cleared"] is False
    assert payload["side_effects_allowed"] is False
    assert payload["substantive_ethics_tested"] is False
    assert payload["complete"] is False


def test_check_bootstrap_human_output_emits_nonproduction_flags(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "scripts").mkdir()
    (repo / "scripts" / "check_bootstrap.py").write_text(
        (ROOT / "scripts" / "check_bootstrap.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (repo / "scripts" / "sync_components.sh").write_text(
        "#!/usr/bin/env bash\n"
        "cat <<'JSON'\n"
        "{\n"
        "  \"schema_version\": \"1.0\",\n"
        "  \"mode\": \"plan-json\",\n"
        "  \"components\": [\n"
        "    {\"name\": \"TrustedRuntime\", \"action\": \"pull\", \"path_state\": \"present\", \"receipt_state\": \"present\"}\n"
        "  ]\n"
        "}\n"
        "JSON\n",
        encoding="utf-8",
        newline="\n",
    )
    (repo / "scripts" / "sync_components.sh").chmod(0o755)

    completed = subprocess.run(
        [sys.executable, str(repo / "scripts" / "check_bootstrap.py")],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "production_cleared=true" in completed.stdout
    assert "substantive_ethics_tested=false" in completed.stdout
