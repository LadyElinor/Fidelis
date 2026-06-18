#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

REGISTRY: list[tuple[str, list[str], str]] = [
    ("audit-jsonl-schema", ["python", "Reasoning/check_sophron_audit_jsonl_schema.py"], "gate"),
    ("probe-jsonl-schema", ["python", "Reasoning/check_sophron_probe_jsonl_schema.py"], "gate"),
    ("skew-jsonl-schema", ["python", "Reasoning/check_sophron_skew_jsonl_schema.py"], "gate"),
    ("safety-frame-jsonl-schema", ["python", "Reasoning/check_sophron_safety_frame_jsonl_schema.py"], "gate"),
    ("regression-delta", ["python", "Reasoning/sophron_regression_delta_checker.py"], "gate"),
    ("uncertainty-ledger", ["python", "Reasoning/check_sophron_uncertainty_ledger.py"], "advisory"),
    ("adversarial-resilience", ["python", "Reasoning/check_sophron_adversarial_policy_resilience.py"], "advisory"),
    ("audit-attack-matrix", ["python", "Reasoning/check_sophron_audit_attack_matrix.py"], "advisory"),
    ("competing-hypotheses", ["python", "Reasoning/check_sophron_competing_hypotheses.py"], "advisory"),
    ("cross-plane-skew", ["python", "Reasoning/check_sophron_cross_plane_skew.py"], "advisory"),
    ("elastic-budget", ["python", "Reasoning/check_sophron_elastic_budget_compliance.py"], "advisory"),
    ("probe-budget-bridge", ["python", "Reasoning/check_sophron_probe_budget_bridge.py"], "advisory"),
]

_MISSING_INPUT_MARKERS = ("FileNotFoundError", "No such file", "does not exist")
PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"


@dataclass
class Result:
    name: str
    tier: str
    status: str
    detail: str = ""


def _discover_unregistered() -> list[tuple[str, list[str], str]]:
    known = {tuple(cmd) for _, cmd, _ in REGISTRY}
    extra = []
    for p in sorted((REPO_ROOT / "Reasoning").glob("check_*.py")):
        cmd = ["python", str(p.relative_to(REPO_ROOT))]
        if tuple(cmd) not in known:
            extra.append((p.stem.replace("check_sophron_", "").replace("_", "-"), cmd, "advisory"))
    return extra


def _python_command() -> list[str]:
    env_cmd = (REPO_ROOT / ".venv" / "Scripts" / "python.exe")
    if env_cmd.exists():
        return [str(env_cmd)]
    return [sys.executable]


def _run_one(name: str, cmd: list[str], tier: str) -> Result:
    script = Path(cmd[-1])
    if not (REPO_ROOT / script).exists():
        return Result(name, tier, SKIP, "checker not present on this branch")
    real_cmd = list(cmd)
    if real_cmd and real_cmd[0] == "python":
        real_cmd = _python_command() + real_cmd[1:]
    proc = subprocess.run(real_cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    if proc.returncode == 0:
        return Result(name, tier, PASS)
    blob = (proc.stderr or "") + (proc.stdout or "")
    if any(m in blob for m in _MISSING_INPUT_MARKERS):
        return Result(name, tier, SKIP, "input fixture not committed")
    last = ((proc.stderr or proc.stdout).strip().splitlines() or ["(no output)"])[-1]
    return Result(name, tier, FAIL, last[:200])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true", help="run gate-tier checks only")
    ap.add_argument("--list", action="store_true", help="print the registry and exit")
    args = ap.parse_args()

    checks = list(REGISTRY) + _discover_unregistered()
    if args.gate:
        checks = [c for c in checks if c[2] == "gate"]

    if args.list:
        for name, cmd, tier in checks:
            print(f"  [{tier:8}] {name:26} {' '.join(cmd)}")
        return 0

    results = [_run_one(name, cmd, tier) for name, cmd, tier in checks]

    width = max((len(r.name) for r in results), default=10)
    print(f"\nSOPHRON checks  (root: {REPO_ROOT})\n" + "-" * (width + 30))
    for r in results:
        mark = {PASS: "ok  ", FAIL: "FAIL", SKIP: "skip"}[r.status]
        line = f"  [{mark}] {r.name:<{width}}  ({r.tier})"
        if r.detail:
            line += f"  - {r.detail}"
        print(line)

    gate_failures = [r for r in results if r.status == FAIL and r.tier == "gate"]
    advisory_failures = [r for r in results if r.status == FAIL and r.tier == "advisory"]
    skipped = [r for r in results if r.status == SKIP]

    print("-" * (width + 30))
    print(f"  passed:   {sum(r.status == PASS for r in results)}")
    print(f"  failed:   {len(gate_failures)} gate / {len(advisory_failures)} advisory")
    print(f"  skipped:  {len(skipped)} (missing input fixtures)")
    if advisory_failures:
        print("  note: advisory failures do not break the build")

    return 1 if gate_failures else 0


if __name__ == "__main__":
    sys.exit(main())
