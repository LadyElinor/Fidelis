from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

import pytest

from efm_council import run_council
from run_regression_harness import compare_expectations, discover_cases, extract_signals, load_expectations


EXPECTATIONS: Dict[str, Dict[str, Any]] = load_expectations()
CASE_MAP: Dict[str, Dict[str, Any]] = {case["id"]: case for case in discover_cases()}
EXPECTED_CASE_IDS: List[str] = sorted(case_id for case_id in EXPECTATIONS.keys() if case_id in CASE_MAP)
MISSING_CASE_IDS: List[str] = sorted(case_id for case_id in EXPECTATIONS.keys() if case_id not in CASE_MAP)


def _run_case(case_id: str) -> Dict[str, Any]:
    case = CASE_MAP[case_id]
    record = run_council(case["prompt"])
    return extract_signals(asdict(record), case_id)


@pytest.mark.parametrize("case_id", EXPECTED_CASE_IDS)
def test_expectation_case_matches_contract(case_id: str) -> None:
    actual = _run_case(case_id)
    expected = EXPECTATIONS[case_id]
    comparison = compare_expectations(actual, expected)
    assert comparison["status"] == "PASS", "; ".join(comparison["notes"])


def test_all_expectation_cases_have_prompts() -> None:
    assert not MISSING_CASE_IDS, f"Expectation cases missing prompt files: {', '.join(MISSING_CASE_IDS)}"


@pytest.mark.parametrize("case_id", EXPECTED_CASE_IDS)
def test_prompt_file_exists_for_expected_case(case_id: str) -> None:
    prompt_path = Path("cases") / f"{case_id}_prompt.txt"
    assert prompt_path.exists(), f"Missing prompt file for expectation case: {case_id}"
