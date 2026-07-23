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
sys.path.insert(0, str(Path(__file__).resolve().parent))

from provenance_utils import sha256_hex_bytes

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
    reason_code: str | None = None
    reason: str | None = None
    expected_artifact: str | None = None
    stdout_path: str | None = None
    stderr_path: str | None = None
    stdout_digest: str | None = None
    stderr_digest: str | None = None
    started_at: str | None = None
    completed_at: str | None = None


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


def _prepare_component(component: str, cwd: Path, command: list[str]) -> tuple[bool, int | None, str | None, str | None, str | None]:
    if component == "cer-telemetry":
        package_json = cwd / "package.json"
        if not package_json.exists():
            return False, None, "missing_component_manifest", f"No package.json exists at {package_json}", str(package_json)
        return True, None, None, None, None
    pyproject = cwd / "pyproject.toml"
    if pyproject.exists() and command[:3] == [sys.executable, "-m", "pytest"]:
        install_command = [sys.executable, "-m", "pip", "install", "-e", "."]
        completed = subprocess.run(install_command, cwd=cwd, check=False, capture_output=True, text=True)
        if completed.returncode != 0:
            return False, completed.returncode, "component_setup_failed", f"Editable install failed for {component}", str(pyproject)
        return True, None, None, None, None
    if component != "sophron-cer":
        return True, None, None, None, None
    if command[:2] != ["npm", "test"]:
        return True, None, None, None, None
    package_json = cwd / "package.json"
    if not package_json.exists():
        return False, None, "missing_component_manifest", f"No package.json exists at {package_json}", str(package_json)
    node_modules = cwd / "node_modules"
    package_lock = cwd / "package-lock.json"
    if node_modules.exists() and package_lock.exists():
        return True, None, None, None, None
    install_command, available = _resolved_command(["npm", "install"])
    if not available:
        return False, None, "missing_node_tool", "npm is required to prepare sophron-cer", None
    completed = subprocess.run(install_command, cwd=cwd, check=False)
    if completed.returncode != 0:
        return False, completed.returncode, "component_setup_failed", "npm install failed while preparing sophron-cer", None
    return True, None, None, None, None


def _component_env(component: str) -> dict[str, str]:
    env = dict(os.environ)
    if component == "trusted-runtime":
        env["TRUSTED_RUNTIME_WORKSPACE_ROOT"] = str(ROOT)
        env["MEANING_ASSAY_SRC"] = str(ROOT / "packages" / "meaning-assay" / "src")
        env["ETHICS_COUNCIL_SRC"] = str(ROOT / "packages" / "ethics-council")
        env["TRUSTWORTHY_AGENT_STACK_SRC"] = str(ROOT / "packages" / "trustworthy-agent-stack")
        env["SOPHRON_CER_SRC"] = str(ROOT / "packages" / "sophron-cer")
        env["ATTEST_AGENT_CONLANG_SRC"] = str(ROOT / "packages" / "attest-agent-conlang")
    return env


def run(component: str, cwd: Path, command: list[str], required_components: set[str]) -> Result:
    reports = ROOT / "reports"
    logs_dir = reports / "component-logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    if not cwd.exists():
        status = "unexpectedly_missing" if component in required_components else "expected_not_applicable"
        return Result(component, command, status, None, "presence")
    prepare_ok, prepare_returncode, reason_code, reason, expected_artifact = _prepare_component(component, cwd, command)
    if not prepare_ok:
        status = "blocked" if component in required_components else f"expected_not_applicable"
        return Result(component, command, status, prepare_returncode, "tooling", reason_code, reason, expected_artifact)
    resolved_command, available = _resolved_command(command)
    if not available:
        status = "blocked" if component in required_components else f"expected_not_applicable"
        return Result(component, command, status, None, "tooling", "missing_runtime_tool", f"Command executable is unavailable: {command[0]}", None)

    started_at = datetime.now(timezone.utc).isoformat()
    completed = subprocess.run(resolved_command, cwd=cwd, check=False, capture_output=True, text=True, env=_component_env(component))
    completed_at = datetime.now(timezone.utc).isoformat()

    stdout_text = completed.stdout or ""
    stderr_text = completed.stderr or ""
    stdout_path = logs_dir / f"{component}.stdout.log"
    stderr_path = logs_dir / f"{component}.stderr.log"
    stdout_path.write_text(stdout_text, encoding="utf-8")
    stderr_path.write_text(stderr_text, encoding="utf-8")

    return Result(
        component,
        command,
        "passed" if completed.returncode == 0 else "failed",
        completed.returncode,
        "execution",
        stdout_path=str(stdout_path.relative_to(ROOT)),
        stderr_path=str(stderr_path.relative_to(ROOT)),
        stdout_digest=sha256_hex_bytes(stdout_text.encode("utf-8")),
        stderr_digest=sha256_hex_bytes(stderr_text.encode("utf-8")),
        started_at=started_at,
        completed_at=completed_at,
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
        detail = f" reason_code={result.reason_code}" if result.reason_code else ""
        print(f"{result.status.upper():<30} {result.component}{detail}")
    print(
        f"PROFILE={args.profile} PRODUCTION_CLEARED=false "
        f"SIDE_EFFECTS_ALLOWED=false SUBSTANTIVE_ETHICS_TESTED=false"
    )
    return 1 if any(result.status in hard_fail_statuses for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
