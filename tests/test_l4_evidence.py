from __future__ import annotations

from trusted_runtime.integration.l4_evidence import build_sophron_validation_envelope


def test_l4_envelope_marks_failed_when_adapter_error_present_even_with_tas_local_validation():
    envelope = build_sophron_validation_envelope(
        sophron_report_valid=False,
        sophron_signals={},
        tas_local_validation={"violations": []},
        sophron_report={},
        sophron_stdout="",
        l4_closure={"closure_complete": False},
        degradation_reason="RuntimeError",
        receipt_linkage=True,
        tas_closure_referenced=True,
    )
    assert envelope.validation_status == "FAILED"
    assert envelope.passed is False


def test_l4_envelope_marks_calibrating_for_partial_nonfailing_sophron_structure():
    envelope = build_sophron_validation_envelope(
        sophron_report_valid=False,
        sophron_signals={"sophron.shift": {"tier": "validated-sim"}},
        tas_local_validation={"violations": []},
        sophron_report={"report": {"signals": {"shift": {"score": 0.4}}}},
        sophron_stdout="",
        l4_closure={"closure_complete": False},
        degradation_reason=None,
        receipt_linkage=True,
        tas_closure_referenced=True,
    )
    assert envelope.validation_status == "CALIBRATING"
    assert envelope.passed is False


def test_l4_envelope_marks_unavailable_for_tas_only_without_any_sophron_structure():
    envelope = build_sophron_validation_envelope(
        sophron_report_valid=False,
        sophron_signals={},
        tas_local_validation={"violations": []},
        sophron_report={},
        sophron_stdout="",
        l4_closure={"closure_complete": False},
        degradation_reason=None,
        receipt_linkage=True,
        tas_closure_referenced=True,
    )
    assert envelope.validation_status == "UNAVAILABLE"
    assert envelope.passed is False
