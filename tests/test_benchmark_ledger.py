from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict

import pytest

from efm_council import run_council
from run_regression_harness import compare_benchmark_ledger, discover_cases, extract_signals, load_benchmark_ledger


BENCHMARK_LEDGER: Dict[str, Dict[str, Any]] = load_benchmark_ledger()
CASE_MAP: Dict[str, Dict[str, Any]] = {case["id"]: case for case in discover_cases()}
BENCHMARK_CASE_IDS = sorted(case_id for case_id in BENCHMARK_LEDGER.keys() if case_id in CASE_MAP)
MISSING_BENCHMARK_CASE_IDS = sorted(case_id for case_id in BENCHMARK_LEDGER.keys() if case_id not in CASE_MAP)


def _run_case(case_id: str) -> Dict[str, Any]:
    case = CASE_MAP[case_id]
    record = run_council(case["prompt"])
    return extract_signals(asdict(record), case_id)


@pytest.mark.parametrize("case_id", BENCHMARK_CASE_IDS)
def test_benchmark_case_matches_ledger(case_id: str) -> None:
    actual = _run_case(case_id)
    comparison = compare_benchmark_ledger(actual, BENCHMARK_LEDGER[case_id])
    assert comparison["status"] == "PASS", "; ".join(comparison["notes"])


def test_benchmark_ledger_cases_have_prompts() -> None:
    assert not MISSING_BENCHMARK_CASE_IDS, f"Benchmark ledger cases missing prompt files: {', '.join(MISSING_BENCHMARK_CASE_IDS)}"
