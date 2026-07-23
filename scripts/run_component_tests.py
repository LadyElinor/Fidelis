#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATHS = {
    "minimal": ROOT / "profiles/minimal.json",
    "all-real": ROOT / "profiles/all-real.json",
}
HARD_FAIL_STATUSES_BY_PROFILE = {
    "minimal": {"failed"},
    "all-real": {"failed", "unexpectedly_missing", "blocked"},
}


@dataclass
class Result:
    component: str
    command: list[str]
    status: str
    returncode: int | None
    classification: str


def _load_profile(name: str) -> dict[str, object]:
    return json.loads(PROFILE_PATHS[name].read_text(encoding="utf-8"))


def _resolved_command(command: list[str]) -> tuple[list[str], bool]:
    executable = command[0]
    if os.name == "nt" and executable in {"npm", "npx"}:
        resolved = shutil.which(f"{executable}.cmd") or shutil.which(executable)
        if resolved is not None:
            return [resolved, *command[1:]], True
        return command, False
    return command, shutil.which(executable) is not None


def _prepare_component(component: str, cwd: Path, command: list[str]) -> tuple[bool, int | None]:
    if component == "cer-telemetry":
        package_json = cwd / "package.json"
        if not package_json.exists():
            return False, None
        return True, None
    if component != "sophron-cer":
        return True, None
    if command[:2] != ["npm", "test"]:
        return True, None
    package_json = cwd / "package.json"
    if not package_json.exists():
        return False, None
    node_modules = cwd / "node_modules"
    package_lock = cwd / "package-lock.json"
    if node_modules.exists() and package_lock.exists():
        return True, None
    install_command, available = _resolved_command(["npm", "install"])
    if not available:
        return False, None
    completed = subprocess.run(install_command, cwd=cwd, check=False)
    return completed.returncode == 0, completed.returncode


def run(component: str, cwd: Path, command: list[str], required_components: set[str]) -> Result:
    if not cwd.exists():
        status = "unexpectedly_missing" if component in required_components else "expected_not_applicable"
        return Result(component, command, status, None, "presence")
    prepare_ok, prepare_returncode = _prepare_component(component, cwd, command)
    if not prepare_ok:
        status = "blocked" if component in required_components else f"expected_not_applicable"
        return Result(component, command, status, prepare_returncode, "tooling")
    resolved_command, available = _resolved_command(command)
    if not available:
        status = "blocked" if component in required_components else f"expected_not_applicable"
        return Result(component, command, status, None, "tooling")
    completed = subprocess.run(resolved_command, cwd=cwd, check=False)
    return Result(
        component,
        command,
        "passed" if completed.returncode == 0 else "failed",
        completed.returncode,
        "execution",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=sorted(PROFILE_PATHS), default="minimal")
    args = parser.parse_args()

    profile = _load_profile(args.profile)
    required_components = set(profile["required_components"])
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
    results = [run(*entry, required_components) for entry in commands]
    hard_fail_statuses = HARD_FAIL_STATUSES_BY_PROFILE[args.profile]
    all_required_passed = not any(result.status in hard_fail_statuses for result in results)

    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile": args.profile,
        "production_cleared": False,
        "substantive_ethics_tested": False,
        "side_effects_allowed": False,
        "components_verified": args.profile == "all-real" and all_required_passed,
        "required_components": sorted(required_components),
        "results": [asdict(result) for result in results],
    }
    (reports / "component-tests.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    for result in results:
        print(f"{result.status.upper():<30} {result.component}")
    print(
        f"PROFILE={args.profile} PRODUCTION_CLEARED=false "
        f"SIDE_EFFECTS_ALLOWED=false SUBSTANTIVE_ETHICS_TESTED=false"
    )
    return 1 if any(result.status in hard_fail_statuses for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
