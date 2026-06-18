#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import yaml

from efm_council import run_council
from report import save_outputs

CASES_DIR = Path("cases")
TESTS_DIR = Path("tests")
EXPECTED_FILE = TESTS_DIR / "BENCHMARK_EXPECTED.json"
EXPECTATIONS_FILE = CASES_DIR / "expectations.yaml"
OUTPUT_DIR = Path("outputs") / "regression"
BENCHMARK_LEDGER_FILE = TESTS_DIR / "BENCHMARK_LEDGER.yaml"

KEY_SIGNALS = [
    "detector_overlap_flag",
    "suspension_triggered",
    "minority_report_required",
    "asymmetric_risk_transfer_risk",
    "actuarial_fairness_gap_risk",
    "methodology_opacity_risk",
    "status_admiration_distortion_risk",
    "stage_one_thinking_risk",
    "self_audit_failure_risk",
    "overall_recommendation_contains",
    "stability_assessment",
]


def load_expected() -> Dict[str, Dict[str, Any]]:
    if not EXPECTED_FILE.exists():
        EXPECTED_FILE.parent.mkdir(parents=True, exist_ok=True)
        EXPECTED_FILE.write_text("{}\n", encoding="utf-8")
        return {}
    return json.loads(EXPECTED_FILE.read_text(encoding="utf-8"))


def load_expectations() -> Dict[str, Dict[str, Any]]:
    if not EXPECTATIONS_FILE.exists():
        return {}
    payload = yaml.safe_load(EXPECTATIONS_FILE.read_text(encoding="utf-8")) or {}
    expectations = payload.get("expectations", {})
    return expectations if isinstance(expectations, dict) else {}


def load_benchmark_ledger() -> Dict[str, Dict[str, Any]]:
    if not BENCHMARK_LEDGER_FILE.exists():
        return {}
    payload = yaml.safe_load(BENCHMARK_LEDGER_FILE.read_text(encoding="utf-8")) or {}
    benchmarks = payload.get("benchmarks", {})
    return benchmarks if isinstance(benchmarks, dict) else {}


def discover_cases() -> List[Dict[str, Any]]:
    prompts = sorted(CASES_DIR.glob("*_prompt.txt"))
    cases: List[Dict[str, Any]] = []
    for prompt_path in prompts:
        case_id = prompt_path.stem.replace("_prompt", "")
        cases.append({
            "id": case_id,
            "prompt_path": prompt_path,
            "prompt": prompt_path.read_text(encoding="utf-8").strip(),
        })
    return cases


def extract_signals(record_dict: Dict[str, Any], case_id: str) -> Dict[str, Any]:
    synth = record_dict["synthesis"]
    path = synth.get("synthesis_path", {})
    ph = record_dict.get("parse_humility", {})
    adaa = synth.get("dissonance_aware_arbitration", {})
    return {
        "case_id": case_id,
        "timestamp": datetime.utcnow().isoformat(),
        "detector_overlap_flag": synth.get("detector_overlap_flag", False),
        "suspension_triggered": path.get("suspension_triggered", False),
        "minority_report_required": synth.get("minority_report_required", False),
        "asymmetric_risk_transfer_risk": path.get("asymmetric_risk_transfer_risk", False),
        "actuarial_fairness_gap_risk": path.get("actuarial_fairness_gap_risk", False),
        "methodology_opacity_risk": path.get("methodology_opacity_risk", False),
        "status_admiration_distortion_risk": path.get("status_admiration_distortion_risk", False),
        "stage_one_thinking_risk": path.get("stage_one_thinking_risk", False),
        "self_audit_failure_risk": path.get("self_audit_failure_risk", False),
        "overall_recommendation": synth.get("overall_recommendation", ""),
        "stability_assessment": synth.get("stability_assessment", ""),
        "mode": adaa.get("synthesis_mode", "standard"),
        "surface_irreconcilable_conflict": len(adaa.get("irreconcilable_dissonance", [])) > 0,
        "triage_level": ph.get("analysis_mode", ""),
        "domains_detected_all": path.get("domains_detected_all", []),
    }


def run_case(case: Dict[str, Any]) -> Dict[str, Any]:
    record = run_council(case["prompt"])
    record_dict = asdict(record)
    out_base = OUTPUT_DIR / case["id"] / case["id"]
    save_outputs(record_dict, str(out_base))
    return extract_signals(record_dict, case["id"])


def compare_results(actual: Dict[str, Any], expected: Dict[str, Any]) -> Dict[str, Any]:
    notes = []
    status = "PASS"
    for key in KEY_SIGNALS:
        if key not in expected:
            continue
        if key == "overall_recommendation_contains":
            needle = expected[key]
            hay = actual.get("overall_recommendation", "")
            if needle not in hay:
                status = "MISMATCH"
                notes.append(f"overall_recommendation missing substring: {needle}")
            continue
        if actual.get(key) != expected[key]:
            status = "MISMATCH"
            notes.append(f"{key}: expected {expected[key]} got {actual.get(key)}")
    return {"case_id": actual["case_id"], "status": status, "notes": notes}


def compare_expectations(actual: Dict[str, Any], expected: Dict[str, Any]) -> Dict[str, Any]:
    notes = []
    status = "PASS"
    if "mode" in expected and actual.get("mode") != expected["mode"]:
        status = "MISMATCH"
        notes.append(f"mode: expected {expected['mode']} got {actual.get('mode')}")
    if "surface_irreconcilable_conflict" in expected and actual.get("surface_irreconcilable_conflict") != expected["surface_irreconcilable_conflict"]:
        status = "MISMATCH"
        notes.append(f"surface_irreconcilable_conflict: expected {expected['surface_irreconcilable_conflict']} got {actual.get('surface_irreconcilable_conflict')}")
    if "suspension_triggered" in expected and actual.get("suspension_triggered") != expected["suspension_triggered"]:
        status = "MISMATCH"
        notes.append(f"suspension_triggered: expected {expected['suspension_triggered']} got {actual.get('suspension_triggered')}")
    if "triage_level" in expected and actual.get("triage_level") != expected["triage_level"]:
        status = "MISMATCH"
        notes.append(f"triage_level: expected {expected['triage_level']} got {actual.get('triage_level')}")
    for forbidden in expected.get("forbidden_domains", []):
        if forbidden in actual.get("domains_detected_all", []):
            status = "MISMATCH"
            notes.append(f"forbidden domain activated: {forbidden}")
    return {"case_id": actual["case_id"], "status": status, "notes": notes}


def compare_benchmark_ledger(actual: Dict[str, Any], benchmark: Dict[str, Any]) -> Dict[str, Any]:
    notes = []
    status = "PASS"
    for key, expected_value in benchmark.get("expected_signals", {}).items():
        if actual.get(key) != expected_value:
            status = "MISMATCH"
            notes.append(f"{key}: expected {expected_value} got {actual.get(key)}")
    return {"case_id": actual["case_id"], "status": status, "notes": notes}


def main() -> None:
    parser = argparse.ArgumentParser(description="EthicsCouncil regression harness")
    parser.add_argument("--cases", nargs="*", help="specific case ids")
    parser.add_argument("--update", action="store_true", help="update baseline from current outputs")
    args = parser.parse_args()

    expected = load_expected()
    expectations = load_expectations()
    benchmark_ledger = load_benchmark_ledger()
    cases = discover_cases()
    if args.cases:
        wanted = {c.upper() for c in args.cases}
        cases = [c for c in cases if c["id"].upper() in wanted]

    results = []
    comparisons = []
    for case in cases:
        result = run_case(case)
        results.append(result)
        if args.update:
            expected[result["case_id"]] = {
                "detector_overlap_flag": result["detector_overlap_flag"],
                "suspension_triggered": result["suspension_triggered"],
                "minority_report_required": result["minority_report_required"],
                "asymmetric_risk_transfer_risk": result["asymmetric_risk_transfer_risk"],
                "actuarial_fairness_gap_risk": result["actuarial_fairness_gap_risk"],
                "methodology_opacity_risk": result["methodology_opacity_risk"],
                "status_admiration_distortion_risk": result["status_admiration_distortion_risk"],
                "stage_one_thinking_risk": result["stage_one_thinking_risk"],
                "self_audit_failure_risk": result["self_audit_failure_risk"],
                "overall_recommendation_contains": result["overall_recommendation"][:80],
                "stability_assessment": result["stability_assessment"],
            }
        elif result["case_id"] in expected:
            comparisons.append(compare_results(result, expected[result["case_id"]]))
        if result["case_id"] in expectations:
            comparisons.append(compare_expectations(result, expectations[result["case_id"]]))
        if result["case_id"] in benchmark_ledger:
            comparisons.append(compare_benchmark_ledger(result, benchmark_ledger[result["case_id"]]))

    if args.update:
        EXPECTED_FILE.parent.mkdir(parents=True, exist_ok=True)
        EXPECTED_FILE.write_text(json.dumps(expected, indent=2), encoding="utf-8")
        print(f"Updated {EXPECTED_FILE} with {len(expected)} cases")

    print("\nREGRESSION REPORT")
    print("Case ID                     Status    Notes")
    print("-" * 80)
    for comp in comparisons:
        notes = "; ".join(comp["notes"]) if comp["notes"] else "-"
        print(f"{comp['case_id']:<27} {comp['status']:<8} {notes}")
    if not comparisons and not args.update:
        print("No baseline comparisons yet. Run with --update first.")


if __name__ == "__main__":
    main()
