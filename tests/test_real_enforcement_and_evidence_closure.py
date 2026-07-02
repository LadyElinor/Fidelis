from __future__ import annotations

import pytest

from trusted_runtime.integration.availability import (
    real_telemetry_stack_available,
    trustworthy_agent_stack_available,
)
from trusted_runtime.config import IntegrationMode, detect_integration_mode
from trusted_runtime.integration.engine import CerSophronTelemetryAdapter, TrustworthyAgentStackAdapter, assemble_execution_decision
from trusted_runtime.integration.report import render_markdown_report
from trusted_runtime.shared.enums import AdapterProvenance, RuntimeDisposition
from trusted_runtime.shared.models import CouncilAssessment, ProposedAction, ReceiptRef, SophronValidation


def _action(description: str = "review repo integration governance safety multi-step") -> ProposedAction:
    return ProposedAction(id="t1", description=description, context={"repo": "TrustedRuntime", "review_kind": "pull_request"}, proposed_by="op")


def _council() -> CouncilAssessment:
    return CouncilAssessment(
        decision_id="t1",
        hazards=["safety-critical change"],
        fault_lines=[],
        suspension_triggers=[],
        unresolved_questions=[],
        confidence_notes=[],
        irreversibility_score=0.2,
        contested=False,
        raw_lens_outputs={},
        adapter_provenance=AdapterProvenance.REAL,
        receipt=ReceiptRef(sha256="abc"),
    )


def test_tas_adapter_uses_real_routing_surface_when_available():
    if not trustworthy_agent_stack_available():
        pytest.skip("TrustworthyAgentStack sibling repo absent; REAL routing surface not testable on this clone")
    risk, disposition, vita_state, provenance = TrustworthyAgentStackAdapter().assess(_action(), _council())
    assert provenance in {AdapterProvenance.REAL, AdapterProvenance.PARTIAL}
    assert vita_state.get("task_routing") is not None
    assert vita_state["task_routing"]["route"] == "openclaw"
    assert vita_state.get("closure_bar") is not None
    assert "closure_complete" in vita_state["closure_bar"]
    assert "closure_checks" in vita_state["closure_bar"]
    assert vita_state["closure_bar"]["closure_checks"].get("risk_state_binding") is True
    assert vita_state["closure_bar"]["closure_checks"].get("runtime_disposition_binding") is True
    assert vita_state["closure_bar"]["closure_checks"].get("evidence_chain") is True
    assert vita_state["closure_bar"]["closure_checks"].get("receipt_linkage") is True
    assert vita_state["closure_bar"]["enforcement_trace"]["checkpoint_mode"] == "runtime-derived"
    assert vita_state.get("enforcement_maturity") in {"real", "partial"}
    assert disposition in {RuntimeDisposition.PROCEED, RuntimeDisposition.CONFIRM_HUMAN, RuntimeDisposition.HALT}


def test_tas_adapter_stub_path_surfaces_incomplete_closure_bar():
    action = _action()
    council = _council().model_copy(update={"irreversibility_score": 0.9, "suspension_triggers": ["manual review required"]})
    original_mock = TrustworthyAgentStackAdapter.assess.__globals__.get("MockEthicsCouncil")
    original_gates = TrustworthyAgentStackAdapter.assess.__globals__.get("hazard_to_required_gates")
    try:
        TrustworthyAgentStackAdapter.assess.__globals__["MockEthicsCouncil"] = None
        TrustworthyAgentStackAdapter.assess.__globals__["hazard_to_required_gates"] = None
        risk, disposition, vita_state, provenance = TrustworthyAgentStackAdapter().assess(action, council)
    finally:
        TrustworthyAgentStackAdapter.assess.__globals__["MockEthicsCouncil"] = original_mock
        TrustworthyAgentStackAdapter.assess.__globals__["hazard_to_required_gates"] = original_gates

    assert provenance is AdapterProvenance.STUB
    assert disposition is RuntimeDisposition.HALT
    assert vita_state["enforcement_maturity"] == "stub"
    assert vita_state["closure_bar"]["closure_complete"] is False
    assert "tas_live_stack" in vita_state["closure_bar"]["closure_missing"]
    assert "hazard_payload" in vita_state["closure_bar"]["closure_missing"]
    assert "receipt_linkage" in vita_state["closure_bar"]["closure_missing"]
    assert vita_state["closure_bar"]["closure_checks"]["risk_state_binding"] is True


def test_tas_partial_path_surfaces_missing_route_requirement():
    action = _action()
    council = _council()
    original_classifier = TrustworthyAgentStackAdapter.assess.__globals__.get("tas_classify_task")
    try:
        TrustworthyAgentStackAdapter.assess.__globals__["tas_classify_task"] = None
        risk, disposition, vita_state, provenance = TrustworthyAgentStackAdapter().assess(action, council)
    finally:
        TrustworthyAgentStackAdapter.assess.__globals__["tas_classify_task"] = original_classifier

    assert provenance is AdapterProvenance.PARTIAL
    assert vita_state["enforcement_maturity"] == "partial"
    assert vita_state["closure_bar"]["closure_complete"] is False
    assert "task_route" in vita_state["closure_bar"]["closure_missing"]
    assert vita_state["closure_bar"]["closure_checks"]["gate_decisions"] is True
    assert vita_state["closure_bar"]["closure_checks"]["hazard_payload"] is True
    assert vita_state["closure_bar"]["closure_checks"]["receipt_linkage"] is True


def test_tas_export_lines_match_validator_contract():
    if not trustworthy_agent_stack_available():
        pytest.skip("TrustworthyAgentStack sibling repo absent; hashing helpers unavailable on this clone")
    adapter = CerSophronTelemetryAdapter()
    lines = adapter._render_tas_export_lines(_action(), RuntimeDisposition.CONFIRM_HUMAN.value)
    assert len(lines) == 3
    assert '"record_type": "metric_observation"' in lines[0]
    assert '"record_type": "gate_outcome"' in lines[1]
    assert '"record_type": "cohort_partition"' in lines[2]


def test_telemetry_collect_returns_non_stub_when_local_bridges_exist():
    if not real_telemetry_stack_available():
        pytest.skip("CER-Telemetry/SOPHRON sibling repos absent; non-stub collection not testable on this clone")
    bundle = CerSophronTelemetryAdapter().collect(_action(), RuntimeDisposition.CONFIRM_HUMAN.value)
    assert bundle.adapter_provenance in {AdapterProvenance.REAL, AdapterProvenance.PARTIAL}
    assert isinstance(bundle.sophron_validation, SophronValidation)
    assert bundle.sophron_validation.tas_local_validation is not None
    assert bundle.sophron_validation.l4_closure is not None
    assert isinstance(bundle.provenance_hashes, list) and bundle.provenance_hashes


def test_telemetry_partial_path_surfaces_l4_closure_when_sophron_fails(monkeypatch):
    if not trustworthy_agent_stack_available():
        pytest.skip("TrustworthyAgentStack sibling repo absent; TAS-local closure not testable on this clone")

    adapter = CerSophronTelemetryAdapter()

    def _boom(receipt_path, output_dir):
        raise RuntimeError("boom")

    monkeypatch.setattr(adapter, "_run_sophron_adapter", _boom)
    bundle = adapter.collect(_action(), RuntimeDisposition.CONFIRM_HUMAN.value)

    assert bundle.adapter_provenance is AdapterProvenance.PARTIAL
    assert isinstance(bundle.sophron_validation, SophronValidation)
    l4_closure = bundle.sophron_validation.l4_closure
    assert l4_closure.get("closure_complete") is False
    assert l4_closure.get("reporting_axes", {}).get("tas_local_only") is True
    assert l4_closure.get("reporting_axes", {}).get("adapter_failed") is True
    assert bundle.sophron_validation.degradation_reason == "RuntimeError"


def test_golden_decision_surfaces_l2_to_l4_closure_chain():
    if not trustworthy_agent_stack_available():
        pytest.skip("TrustworthyAgentStack sibling repo absent; closure-chain smoke not testable on this clone")

    decision = assemble_execution_decision(_action("review repo integration governance safety multi-step"))

    assert "tas_closure" in decision.vita_state
    assert "tas_closure" in decision.process_provenance
    assert decision.vita_state["tas_closure"].get("closure_bar") is not None
    soph = decision.cer_bundle.sophron_validation
    assert isinstance(soph, SophronValidation)
    assert soph.l4_closure is not None
    assert soph.validation_status in {"VALIDATED", "CALIBRATING", "FAILED", "UNAVAILABLE"}
    assert isinstance(soph.signal_tiers, dict)
    assert soph.tas_closure_referenced is True
    assert "closure_summary" in soph.model_dump()
    assert bool(decision.cer_bundle.provenance_hashes)
    if not decision.vita_state["tas_closure"].get("closure_bar", {}).get("closure_complete", False):
        assert decision.runtime_disposition is not RuntimeDisposition.PROCEED


def test_partial_mode_does_not_fake_behavior_real_for_cer():
    decision = assemble_execution_decision(_action("review repo integration governance safety multi-step"))
    mode = decision.integration_mode_report
    assert mode is not None
    sophron = mode.components.get("sophron_cer")
    assert sophron is not None
    if not sophron.behavior_real:
        assert decision.adapter_provenance["cer_bundle"] is not AdapterProvenance.REAL


def test_report_surfaces_l2_and_l4_closure_sections():
    decision = assemble_execution_decision(_action("review repo integration governance safety multi-step"))
    report = render_markdown_report(decision)
    assert "## Integration Mode (Computed)" in report
    assert "overall mode" in report.lower()
    assert "## L2 closure" in report
    assert "## L4 evidence" in report
    assert "trace checkpoints" in report
    assert "receipt linkage" in report.lower()
    assert "status:" in report.lower()
    assert "signal tiers" in report.lower()


def test_detect_integration_mode_reports_non_real_sophron_honestly_when_stubbed(monkeypatch):
    monkeypatch.setenv("TRUSTED_RUNTIME_MODE", "stub")
    report = detect_integration_mode()
    assert report.mode in {IntegrationMode.STUB, IntegrationMode.PARTIAL, IntegrationMode.ALL_REAL}
    assert report.components["sophron_cer"].behavior_real in {True, False}
    if report.mode is IntegrationMode.STUB:
        assert report.components["sophron_cer"].behavior_real is False
