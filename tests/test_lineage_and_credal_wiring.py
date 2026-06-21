"""Tests for lineage/correlation modeling and its wiring into the engine."""
from __future__ import annotations

import pytest

from trusted_runtime.integration.engine import DEFAULT_ADAPTER_LINEAGES, assemble_execution_decision
from trusted_runtime.shared.lineage import (
    LineageDescriptor,
    correlation_report,
    independence_classes,
    weakest_independence_for_credal,
)
from trusted_runtime.shared.models import ProposedAction

A = LineageDescriptor(author_id="alice", framework_lineage="phi-k", source_lineage="repoA")
A2 = LineageDescriptor(author_id="alice", framework_lineage="phi-k", source_lineage="repoB")
B = LineageDescriptor(author_id="bob", framework_lineage="other", source_lineage="repoC")


def test_same_author_collapses_to_one_class():
    assert len(independence_classes([A, A2])) == 1


def test_distinct_families_two_classes():
    assert len(independence_classes([A, B])) == 2


def test_transitive_collapse_via_shared_framework():
    c = LineageDescriptor(author_id="carol", framework_lineage="phi-k", source_lineage="repoD")
    assert len(independence_classes([A, A2, c])) == 1


def test_report_same_family_not_certification_grade():
    rep = correlation_report({"council": A, "warrant": A2})
    assert rep["n_independence_classes"] == 1
    assert rep["certification_grade_corroboration"] is False
    assert rep["weakest_independence"] == "same-operator"
    assert rep["notes"]


def test_report_mixed_family_is_certification_grade():
    rep = correlation_report({"council": A, "warrant": B})
    assert rep["n_independence_classes"] == 2
    assert rep["certification_grade_corroboration"] is True
    assert rep["weakest_independence"] == "independent-third-party"


def test_default_tr_adapters_are_one_family():
    rep = correlation_report(DEFAULT_ADAPTER_LINEAGES)
    assert rep["certification_grade_corroboration"] is False


def test_reviewer_independence_unverified_by_default():
    assert correlation_report({"council": A})["human_reviewer_independence"] == "unverified"


def test_weakest_independence_helper():
    assert weakest_independence_for_credal({"weakest_independence": "same-operator"}) == "same-operator"
    assert weakest_independence_for_credal({}) == "same-operator"


def _action() -> ProposedAction:
    return ProposedAction(id="t1", description="x", context={}, proposed_by="op")


def test_engine_emits_correlation_report_and_flags_collapse():
    d = assemble_execution_decision(_action())
    assert d.correlation_report is not None
    assert d.correlation_report["certification_grade_corroboration"] is False
    assert any("independent corroboration" in q for q in d.unresolved_questions)


def test_detector_tripwires_get_vacuous_credal_under_same_hand_evidence():
    d = assemble_execution_decision(_action())
    detectors = [
        tw for tw in d.tripwire_records
        if tw.tripwire_id in {"tripwire.ethics_council_hazard", "tripwire.meaning_assay_warrant"}
    ]
    assert detectors, "expected detector tripwires present"
    for tw in detectors:
        assert tw.credal is not None
        assert tw.credal.width == pytest.approx(1.0)


def test_blocking_policy_tripwires_remain_ungated():
    d = assemble_execution_decision(_action())
    blockers = [tw for tw in d.tripwire_records if tw.allowed_for_blocking]
    assert blockers
    for tw in blockers:
        assert tw.credal is None
