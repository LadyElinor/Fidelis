from __future__ import annotations

import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from trusted_runtime.integration.adapters import AdapterSet, HazardAdapter, TelemetryAdapter, WarrantAdapter
from trusted_runtime.integration.integrity import classify_decision_integrity
from trusted_runtime.integration.policy import guard_runtime_disposition
from trusted_runtime.integration.provenance import process_provenance_record
from trusted_runtime.integration.translation import derive_meaning_case_key
from trusted_runtime.shared.enums import (
    AdapterProvenance,
    DecisionIntegrity,
    NormativeSummary,
    ReceiptSchemaVersion,
    RiskState,
    RuntimeDisposition,
)
from trusted_runtime.shared.models import (
    CERRecordBundle,
    CouncilAssessment,
    ExecutionDecision,
    ProposedAction,
    ReceiptRef,
    ReconciliationRecord,
    WarrantAssay,
)
from trusted_runtime.shared.receipts import sha256_hex, strip_receipt_timestamps


def _candidate_meaning_assay_paths() -> list[Path]:
    env_raw = os.environ.get("MEANING_ASSAY_SRC", "")
    candidates: list[Path] = []
    if env_raw:
        candidates.append(Path(env_raw).expanduser())
    candidates.append(Path(__file__).resolve().parents[4] / "27assay" / "meaning-assay" / "src")
    return candidates


def _candidate_ethics_council_paths() -> list[Path]:
    env_raw = os.environ.get("ETHICS_COUNCIL_SRC", "")
    candidates: list[Path] = []
    if env_raw:
        candidates.append(Path(env_raw).expanduser())
    candidates.append(Path(__file__).resolve().parents[4] / "EthicsCouncil")
    return candidates


_MEANING_ASSAY_SRC = next((path for path in _candidate_meaning_assay_paths() if path.exists()), None)
if _MEANING_ASSAY_SRC is not None and str(_MEANING_ASSAY_SRC) not in sys.path:
    sys.path.insert(0, str(_MEANING_ASSAY_SRC))

_ETHICS_COUNCIL_SRC = next((path for path in _candidate_ethics_council_paths() if path.exists()), None)
if _ETHICS_COUNCIL_SRC is not None and str(_ETHICS_COUNCIL_SRC) not in sys.path:
    sys.path.insert(0, str(_ETHICS_COUNCIL_SRC))

try:
    import efm_council
except Exception:
    efm_council = None

try:
    from meaning_assay import analyze, receipt as meaning_assay_receipt
    from meaning_assay.bridge import CouncilOutput, CouncilVerdict, reconcile, warrant_assay_record
    from meaning_assay.cases import get as get_meaning_case
except Exception:
    analyze = None
    meaning_assay_receipt = None
    CouncilOutput = None
    CouncilVerdict = None
    reconcile = None
    warrant_assay_record = None
    get_meaning_case = None


class EthicsCouncilAdapter(HazardAdapter):
    def assess(self, action: ProposedAction) -> CouncilAssessment:
        if efm_council is None:
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
                confidence_notes=["EthicsCouncil unavailable, stubbed hazard output used"],
                irreversibility_score=payload["irreversibility_score"],
                contested=True,
                raw_lens_outputs={"stub": payload},
                adapter_provenance=AdapterProvenance.STUB,
                receipt=ReceiptRef(sha256=sha256_hex(payload), schema_version=ReceiptSchemaVersion.V1_0_0),
            )

        record = efm_council.run_council(action.description)
        payload = asdict(record)
        synthesis = payload["synthesis"]
        risk = payload["risk"]
        convergence_map = synthesis.get("convergence_map", [])
        fault_lines = synthesis.get("fault_lines", [])
        instrumentation = synthesis.get("instrumentation", {})
        hazards = [
            item.get("trigger_family", "unknown_hazard")
            for item in instrumentation.get("hazards", [])
            if isinstance(item, dict)
        ]
        if not hazards:
            hazards = [item.get("point", "council detected nontrivial risk") for item in convergence_map if isinstance(item, dict)]
        return CouncilAssessment(
            decision_id=action.id,
            hazards=hazards,
            convergences=[item.get("point", "") for item in convergence_map if isinstance(item, dict)],
            fault_lines=[item.get("fault_line", "") for item in fault_lines if isinstance(item, dict)],
            suspension_triggers=[
                "EthicsCouncil suspension protocol triggered"
                if synthesis.get("suspension_protocol_triggered")
                else ""
            ] if synthesis.get("suspension_protocol_triggered") else [],
            minority_reports=["Minority report required by council synthesis"] if synthesis.get("minority_report_required") else [],
            unresolved_questions=list(synthesis.get("unresolved_questions", [])),
            confidence_notes=[instrumentation.get("epistemic_status", {}).get("analysis_constraint", "")],
            irreversibility_score=float(risk.get("irreversibility_risk", 0.0)),
            contested=bool(synthesis.get("unresolved_ethical_tension") or synthesis.get("minority_report_required")),
            raw_lens_outputs=payload,
            adapter_provenance=AdapterProvenance.REAL,
            receipt=ReceiptRef(
                sha256=sha256_hex(strip_receipt_timestamps(payload)),
                schema_version=ReceiptSchemaVersion.V1_0_0,
                path=str(_ETHICS_COUNCIL_SRC) if _ETHICS_COUNCIL_SRC is not None else None,
            ),
        )


class MeaningAssayAdapter(WarrantAdapter):
    def assess(self, action: ProposedAction) -> WarrantAssay:
        case_key, translation_notes = derive_meaning_case_key(action.description, action.context)
        if (
            analyze is not None
            and meaning_assay_receipt is not None
            and get_meaning_case is not None
            and case_key
        ):
            case = get_meaning_case(case_key)
            analysis = analyze(case)
            rec = meaning_assay_receipt(case)
            return WarrantAssay(
                decision_id=action.id,
                significance=analysis.significance,
                warrant=analysis.warrant,
                normative_summary=NormativeSummary(analysis.quadrant)
                if analysis.quadrant in {item.value for item in NormativeSummary}
                else NormativeSummary.UNDETERMINED,
                failure_modes=list(analysis.failure_tripped_keys),
                pair_contrasts={"source_case": case_key, "translation_notes": translation_notes},
                confidence_notes=[f"Real meaning-assay adapter used local case '{case_key}'"],
                unresolved_questions=[
                    "Warrant band is contested and may require human interpretive review"
                ]
                if analysis.warrant_band == "contested"
                else [],
                contested=analysis.warrant_band == "contested",
                adapter_provenance=AdapterProvenance.REAL,
                receipt=ReceiptRef(
                    sha256=rec["receipt_sha256"],
                    schema_version=ReceiptSchemaVersion.V1_0_0,
                    path=f"meaning-assay://receipt/{case_key}",
                ),
            )

        payload = {
            "layer": "meaning_assay_stub",
            "decision_id": action.id,
            "significance": 0.95,
            "warrant": -0.6,
            "normative_summary": NormativeSummary.DANGEROUS.value,
            "translation_notes": translation_notes,
        }
        return WarrantAssay(
            decision_id=action.id,
            significance=payload["significance"],
            warrant=payload["warrant"],
            normative_summary=NormativeSummary.DANGEROUS,
            failure_modes=["warrant gap in safety-critical modification"],
            pair_contrasts={"translation_notes": translation_notes},
            confidence_notes=["meaning-assay unavailable or unmapped, stubbed warrant output used"],
            unresolved_questions=["Does the act preserve human review at the right boundary?"],
            contested=True,
            adapter_provenance=AdapterProvenance.STUB,
            receipt=ReceiptRef(sha256=sha256_hex(payload), schema_version=ReceiptSchemaVersion.V1_0_0),
        )


class StubTelemetryAdapter(TelemetryAdapter):
    def collect(self, action: ProposedAction, runtime_disposition: str) -> CERRecordBundle:
        payload = {
            "layer": "cer_stub",
            "execution_id": action.id,
            "runtime_disposition": runtime_disposition,
            "invariants_checked": [{"invariant": "safety_critical", "status": "VIOLATED"}],
        }
        return CERRecordBundle(
            execution_id=action.id,
            state_vectors=[{"t": 0, "state": "proposal_received"}, {"t": 1, "state": runtime_disposition}],
            invariants_checked=payload["invariants_checked"],
            provenance_hashes=[sha256_hex({"action_id": action.id, "layer": "proposal"})],
            sophron_validation={"passed": False, "details": "drift detected in stubbed scenario"},
            confidence_notes=["Stubbed CER/SOPHRON output, replace with real adapter"],
            adapter_provenance=AdapterProvenance.STUB,
            receipt=ReceiptRef(sha256=sha256_hex(payload), schema_version=ReceiptSchemaVersion.V1_0_0),
        )


def default_adapters() -> AdapterSet:
    return AdapterSet(
        hazard=EthicsCouncilAdapter(),
        warrant=MeaningAssayAdapter(),
        telemetry=StubTelemetryAdapter(),
    )


def run_tas_gate(council: CouncilAssessment) -> tuple[RiskState, RuntimeDisposition, dict[str, Any]]:
    severe_hazard_count = len(council.hazards)
    if council.irreversibility_score > 0.7 or council.suspension_triggers:
        return (
            RiskState.RED,
            RuntimeDisposition.HALT,
            {"risk": "RED", "evidence_chain": ["council_hazard", "suspension_trigger"]},
        )
    if severe_hazard_count >= 3 or council.contested or council.minority_reports:
        return (
            RiskState.AMBER,
            RuntimeDisposition.CONFIRM_HUMAN,
            {"risk": "AMBER", "evidence_chain": ["council_hazard_density", "council_contestation"]},
        )
    return (
        RiskState.GREEN,
        RuntimeDisposition.PROCEED,
        {"risk": "GREEN", "evidence_chain": ["no blocking triggers"]},
    )


def _map_council_verdict(runtime_disposition: RuntimeDisposition):
    if CouncilVerdict is None:
        return None
    mapping = {
        RuntimeDisposition.PROCEED: CouncilVerdict.ALLOW,
        RuntimeDisposition.CONFIRM_HUMAN: CouncilVerdict.REVIEW,
        RuntimeDisposition.SUSPEND: CouncilVerdict.ESCALATE,
        RuntimeDisposition.HALT: CouncilVerdict.REFUSE,
    }
    return mapping[runtime_disposition]


def _build_reconciliation(
    action: ProposedAction,
    runtime_disposition: RuntimeDisposition,
    warrant: WarrantAssay | None,
) -> ReconciliationRecord | None:
    if (
        warrant is None
        or reconcile is None
        or CouncilOutput is None
        or CouncilVerdict is None
        or get_meaning_case is None
        or warrant_assay_record is None
    ):
        return None

    source_case = None
    if warrant.pair_contrasts:
        source_case = warrant.pair_contrasts.get("source_case")
    if not source_case:
        return None

    analysis_case = get_meaning_case(source_case)
    council_output = CouncilOutput(case_key=source_case, verdict=_map_council_verdict(runtime_disposition))
    reconciliation = reconcile(council_output, analyze(analysis_case))
    assay_record = warrant_assay_record(
        analysis_case,
        council_output,
        step_id=action.id,
        assay_id=f"wa_{action.id}",
        timestamp=action.timestamp.isoformat(),
    )
    return ReconciliationRecord(
        case_key=source_case,
        council_verdict=reconciliation.council_verdict.name,
        warranted_action=reconciliation.warranted_action.name,
        alignment=reconciliation.alignment,
        rationale=reconciliation.rationale,
        receipt=ReceiptRef(
            sha256=assay_record["record_sha256"],
            schema_version=ReceiptSchemaVersion.V1_0_0,
            path=f"meaning-assay://reconcile/{source_case}",
        ),
    )


def assemble_execution_decision(action: ProposedAction, adapters: AdapterSet | None = None) -> ExecutionDecision:
    adapters = adapters or default_adapters()

    council = adapters.hazard.assess(action)
    risk_state, runtime_disposition, vita_state = run_tas_gate(council)
    warrant = adapters.warrant.assess(action)
    cer_bundle = adapters.telemetry.collect(action, runtime_disposition.value)

    adapter_provenance = {
        "council": council.adapter_provenance,
        "warrant": warrant.adapter_provenance,
        "cer_bundle": cer_bundle.adapter_provenance,
    }
    runtime_disposition, guard_note = guard_runtime_disposition(runtime_disposition, adapter_provenance)
    if guard_note is not None:
        vita_state = {**vita_state, "provenance_guard": guard_note}

    decision_integrity = DecisionIntegrity(classify_decision_integrity(adapter_provenance))
    reconciliation = _build_reconciliation(action, runtime_disposition, warrant)

    confidence_notes: list[str] = []
    unresolved_questions: list[str] = []
    contested = council.contested or cer_bundle.adapter_provenance is not AdapterProvenance.REAL
    if warrant is not None:
        contested = contested or warrant.contested
        confidence_notes.extend(warrant.confidence_notes)
        unresolved_questions.extend(warrant.unresolved_questions)
    confidence_notes.extend([note for note in council.confidence_notes if note])
    confidence_notes.extend(cer_bundle.confidence_notes)
    unresolved_questions.extend(council.unresolved_questions)
    if any(provenance is not AdapterProvenance.REAL for provenance in adapter_provenance.values()):
        unresolved_questions.append("One or more layers remain stubbed or unavailable; decision should not be treated as fully independent")
    if reconciliation is not None:
        confidence_notes.append(f"Reconciliation alignment: {reconciliation.alignment}")

    process_provenance = {
        "council": process_provenance_record(
            adapter_name="EthicsCouncilAdapter",
            adapter_provenance=council.adapter_provenance,
            adapter_version="0.1-local",
            adapter_path=str(_ETHICS_COUNCIL_SRC) if _ETHICS_COUNCIL_SRC else None,
            source_payload=strip_receipt_timestamps(council.model_dump(mode="json")),
        ),
        "warrant": process_provenance_record(
            adapter_name="MeaningAssayAdapter",
            adapter_provenance=warrant.adapter_provenance,
            adapter_version="0.1-local",
            adapter_path=str(_MEANING_ASSAY_SRC) if _MEANING_ASSAY_SRC else None,
            source_payload=strip_receipt_timestamps(warrant.model_dump(mode="json")),
        ),
        "cer_bundle": process_provenance_record(
            adapter_name="StubTelemetryAdapter",
            adapter_provenance=cer_bundle.adapter_provenance,
            adapter_version="0.1-local",
            adapter_path=None,
            source_payload=strip_receipt_timestamps(cer_bundle.model_dump(mode="json")),
        ),
    }

    master_payload = strip_receipt_timestamps(
        {
            "action": action.model_dump(mode="json"),
            "council": council.model_dump(mode="json"),
            "warrant": warrant.model_dump(mode="json") if warrant is not None else None,
            "cer_bundle": cer_bundle.model_dump(mode="json"),
            "risk_state": risk_state.value,
            "runtime_disposition": runtime_disposition.value,
            "vita_state": vita_state,
            "adapter_provenance": {key: value.value for key, value in adapter_provenance.items()},
            "decision_integrity": decision_integrity.value,
            "process_provenance": process_provenance,
            "reconciliation": reconciliation.model_dump(mode="json") if reconciliation is not None else None,
        }
    )

    return ExecutionDecision(
        action_id=action.id,
        council=council,
        warrant=warrant,
        cer_bundle=cer_bundle,
        vita_state=vita_state,
        risk_state=risk_state,
        runtime_disposition=runtime_disposition,
        normative_summary=warrant.normative_summary if warrant is not None else NormativeSummary.UNDETERMINED,
        confidence_notes=confidence_notes,
        unresolved_questions=unresolved_questions,
        contested=contested,
        decision_integrity=decision_integrity,
        adapter_provenance=adapter_provenance,
        process_provenance=process_provenance,
        reconciliation=reconciliation,
        overall_receipt=ReceiptRef(sha256=sha256_hex(master_payload), schema_version=ReceiptSchemaVersion.V1_0_0),
    )
