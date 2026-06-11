from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from trusted_runtime.shared.enums import NormativeSummary, ReceiptSchemaVersion, RiskState, RuntimeDisposition
from trusted_runtime.shared.models import (
    CERRecordBundle,
    CouncilAssessment,
    ExecutionDecision,
    ProposedAction,
    ReceiptRef,
    WarrantAssay,
)
from trusted_runtime.shared.receipts import sha256_hex


_MEANING_ASSAY_SRC = Path(r"C:\Users\arren\.openclaw\workspace\27assay\meaning-assay\src")
if str(_MEANING_ASSAY_SRC) not in sys.path:
    sys.path.insert(0, str(_MEANING_ASSAY_SRC))

try:
    from meaning_assay import analyze, receipt as meaning_assay_receipt
    from meaning_assay.cases import get as get_meaning_case
except Exception:
    analyze = None
    meaning_assay_receipt = None
    get_meaning_case = None


# These stub functions exist only to make the contract executable.
# They should be replaced incrementally with real adapters, ideally in this order:
# 1. meaning-assay
# 2. EthicsCouncil
# 3. TrustworthyAgentStack
# 4. CER/SOPHRON adapters


def run_ethics_council(action: ProposedAction) -> CouncilAssessment:
    """Expected real interface:
    input: ProposedAction-like decision prompt/context
    output: prospective hazard map with fault lines, suspension triggers, and receipt
    """
    payload = {
        "layer": "ethics_council_stub",
        "decision_id": action.id,
        "hazards": ["potential invariant violation"],
        "fault_lines": ["safety-critical change"],
        "irreversibility_score": 0.85,
    }
    return CouncilAssessment(
        decision_id=action.id,
        hazards=payload["hazards"],
        fault_lines=payload["fault_lines"],
        suspension_triggers=["safety-critical invariant changed without human confirmation"],
        unresolved_questions=["Was the invariant modification independently reviewed?"],
        confidence_notes=["Stubbed hazard output, replace with real EthicsCouncil adapter"],
        irreversibility_score=payload["irreversibility_score"],
        contested=True,
        raw_lens_outputs={"stub": payload},
        receipt=ReceiptRef(
            sha256=sha256_hex(payload),
            schema_version=ReceiptSchemaVersion.V1_0_0,
        ),
    )


def run_tas_gate(council: CouncilAssessment) -> tuple[RiskState, RuntimeDisposition, dict[str, Any]]:
    """Expected real interface:
    input: hazard output + runtime context
    output: risk state, runtime disposition, and evidence branch details
    """
    if council.irreversibility_score > 0.7 or council.suspension_triggers:
        return (
            RiskState.RED,
            RuntimeDisposition.HALT,
            {"risk": "RED", "evidence_chain": ["council_hazard", "suspension_trigger"]},
        )
    return (
        RiskState.GREEN,
        RuntimeDisposition.PROCEED,
        {"risk": "GREEN", "evidence_chain": ["no blocking triggers"]},
    )


def run_warrant_assay(action: ProposedAction) -> WarrantAssay:
    """Expected real interface:
    input: ProposedAction rendered into an assayable act representation
    output: significance/warrant interpretation plus receipt

    Current real adapter status:
    - if meaning-assay is available, use a mapped local case
    - otherwise fall back to the scaffold stub
    """
    mapped_case_key = action.context.get("meaning_case_key") if isinstance(action.context, dict) else None
    if analyze is not None and meaning_assay_receipt is not None and get_meaning_case is not None and mapped_case_key:
        case = get_meaning_case(mapped_case_key)
        analysis = analyze(case)
        rec = meaning_assay_receipt(case)
        failure_modes = list(analysis.failure_tripped_keys)
        confidence_notes = [
            f"Real meaning-assay adapter used local case '{mapped_case_key}'",
        ]
        unresolved_questions: list[str] = []
        if analysis.warrant_band == "contested":
            unresolved_questions.append("Warrant band is contested and may require human interpretive review")
        return WarrantAssay(
            decision_id=action.id,
            significance=analysis.significance,
            warrant=analysis.warrant if analysis.warrant is not None else 0.0,
            normative_summary=NormativeSummary(analysis.quadrant) if analysis.quadrant in {item.value for item in NormativeSummary} else NormativeSummary.UNDETERMINED,
            failure_modes=failure_modes,
            pair_contrasts={"source_case": mapped_case_key},
            confidence_notes=confidence_notes,
            unresolved_questions=unresolved_questions,
            contested=analysis.warrant_band == "contested",
            receipt=ReceiptRef(
                sha256=rec["receipt_sha256"],
                schema_version=ReceiptSchemaVersion.V1_0_0,
                path=f"meaning-assay://receipt/{mapped_case_key}",
            ),
        )

    payload = {
        "layer": "meaning_assay_stub",
        "decision_id": action.id,
        "significance": 0.95,
        "warrant": -0.6,
        "normative_summary": NormativeSummary.DANGEROUS.value,
    }
    return WarrantAssay(
        decision_id=action.id,
        significance=payload["significance"],
        warrant=payload["warrant"],
        normative_summary=NormativeSummary.DANGEROUS,
        failure_modes=["warrant gap in safety-critical modification"],
        confidence_notes=["Stubbed warrant output, replace with real meaning-assay adapter"],
        unresolved_questions=["Does the act preserve human review at the right boundary?"],
        contested=True,
        receipt=ReceiptRef(
            sha256=sha256_hex(payload),
            schema_version=ReceiptSchemaVersion.V1_0_0,
        ),
    )


def run_cer_bundle(action: ProposedAction, disposition: RuntimeDisposition) -> CERRecordBundle:
    """Expected real interface:
    input: execution branch and telemetry artifacts
    output: evidence bundle with invariants and SOPHRON validation
    """
    payload = {
        "layer": "cer_stub",
        "execution_id": action.id,
        "runtime_disposition": disposition.value,
        "invariants_checked": [{"invariant": "safety_critical", "status": "VIOLATED"}],
    }
    return CERRecordBundle(
        execution_id=action.id,
        state_vectors=[{"t": 0, "state": "proposal_received"}, {"t": 1, "state": disposition.value}],
        invariants_checked=payload["invariants_checked"],
        provenance_hashes=[sha256_hex({"action_id": action.id, "layer": "proposal"})],
        soprhon_validation={"passed": False, "details": "drift detected in stubbed scenario"},
        confidence_notes=["Stubbed CER/SOPHRON output, replace with real adapter"],
        receipt=ReceiptRef(
            sha256=sha256_hex(payload),
            schema_version=ReceiptSchemaVersion.V1_0_0,
        ),
    )


def assemble_execution_decision(action: ProposedAction) -> ExecutionDecision:
    council = run_ethics_council(action)
    risk_state, runtime_disposition, vita_state = run_tas_gate(council)
    warrant = run_warrant_assay(action)
    cer_bundle = run_cer_bundle(action, runtime_disposition)

    master_payload = {
        "action": action.model_dump(mode="json"),
        "council": council.model_dump(mode="json"),
        "warrant": warrant.model_dump(mode="json"),
        "cer_bundle": cer_bundle.model_dump(mode="json"),
        "risk_state": risk_state.value,
        "runtime_disposition": runtime_disposition.value,
        "vita_state": vita_state,
    }

    return ExecutionDecision(
        action_id=action.id,
        council=council,
        warrant=warrant,
        cer_bundle=cer_bundle,
        vita_state=vita_state,
        risk_state=risk_state,
        runtime_disposition=runtime_disposition,
        normative_summary=warrant.normative_summary,
        confidence_notes=[
            "High hazard and negative warrant in the golden scenario",
            "Warrant is produced by a real meaning-assay adapter path when a case key is supplied",
            "Overall result remains partial-integration until hazard, enforcement, and telemetry adapters replace stubs",
        ],
        unresolved_questions=[
            "Should invariant modifications always require human confirmation even under apparently safe diffs?",
        ],
        contested=True,
        overall_receipt=ReceiptRef(
            sha256=sha256_hex(master_payload),
            schema_version=ReceiptSchemaVersion.V1_0_0,
        ),
    )
