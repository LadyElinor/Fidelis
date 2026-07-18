#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Result:
    component: str
    command: list[str]
    status: str
    returncode: int | None


def run(component: str, cwd: Path, command: list[str]) -> Result:
    if not cwd.exists():
        return Result(component, command, "not_imported", None)
    executable = command[0]
    if shutil.which(executable) is None:
        return Result(component, command, f"missing_executable:{executable}", None)
    completed = subprocess.run(command, cwd=cwd, check=False)
    return Result(component, command, "passed" if completed.returncode == 0 else "failed", completed.returncode)


def main() -> int:
    commands: list[tuple[str, Path, list[str]]] = [
        ("fidelis-contracts", ROOT / "packages/fidelis-contracts", [sys.executable, "-m", "pytest", "-q"]),
        ("aconstellation", ROOT / "packages/aconstellation", [sys.executable, "-m", "pytest", "-q"]),
        ("trusted-runtime", ROOT / "packages/trusted-runtime", [sys.executable, "-m", "pytest", "-q"]),
        ("meaning-assay", ROOT / "packages/meaning-assay", [sys.executable, "-m", "pytest", "-q"]),
        ("attest-agent-conlang", ROOT / "packages/attest-agent-conlang", [sys.executable, "-m", "pytest", "-q"]),
        ("trustworthy-agent-stack", ROOT / "packages/trustworthy-agent-stack", [sys.executable, "-m", "pytest", "-q", "tests"]),
        ("ethics-council", ROOT / "packages/ethics-council", [sys.executable, "-m", "pytest", "-q"]),
        ("cer-telemetry", ROOT / "packages/cer-telemetry", ["npm", "test"]),
        ("sophron-cer", ROOT / "packages/sophron-cer", ["npm", "test"]),
    ]
    results = [run(*entry) for entry in commands]
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results": [asdict(result) for result in results],
    }
    (reports / "component-tests.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    for result in results:
        print(f"{result.status.upper():<30} {result.component}")
    return 1 if any(result.status == "failed" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
