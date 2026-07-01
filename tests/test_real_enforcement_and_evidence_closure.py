from __future__ import annotations

import pytest

from trusted_runtime.integration.availability import (
    real_telemetry_stack_available,
    trustworthy_agent_stack_available,
)
from trusted_runtime.integration.engine import CerSophronTelemetryAdapter, TrustworthyAgentStackAdapter
from trusted_runtime.shared.enums import AdapterProvenance, RuntimeDisposition
from trusted_runtime.shared.models import CouncilAssessment, ProposedAction, ReceiptRef


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
    assert provenance is AdapterProvenance.REAL
    assert vita_state.get("task_routing") is not None
    assert vita_state["task_routing"]["route"] == "openclaw"
    assert disposition in {RuntimeDisposition.PROCEED, RuntimeDisposition.CONFIRM_HUMAN, RuntimeDisposition.HALT}


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
    assert bundle.adapter_provenance is AdapterProvenance.REAL
    assert bundle.sophron_validation.get("tas_local_validation") is not None
    assert isinstance(bundle.provenance_hashes, list) and bundle.provenance_hashes
