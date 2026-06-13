from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

from trusted_runtime.integration.adapters import AdapterSet, HazardAdapter, TelemetryAdapter, WarrantAdapter
from trusted_runtime.integration.formation import assess_formation_hazard
from trusted_runtime.integration.hazard_taxonomy import build_hazard_profile
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


def _first_existing_path(env_var: str, candidates: list[Path]) -> Path | None:
    env_raw = os.environ.get(env_var, "")
    if env_raw:
        candidates = [Path(env_raw).expanduser(), *candidates]
    return next((path for path in candidates if path.exists()), None)


def _candidate_meaning_assay_paths() -> list[Path]:
    return [Path(__file__).resolve().parents[4] / "27assay" / "meaning-assay" / "src"]


def _candidate_ethics_council_paths() -> list[Path]:
    return [Path(__file__).resolve().parents[4] / "EthicsCouncil"]


def _candidate_tas_paths() -> list[Path]:
    root = Path(__file__).resolve().parents[4]
    return [
        root / "repos" / "TrustworthyAgentStack-clean",
        root / "repos" / "TrustworthyAgentStack",
    ]


def _candidate_sophron_paths() -> list[Path]:
    root = Path(__file__).resolve().parents[4]
    return [
        root / "repos" / "SOPHRON-CER-clean",
        Path.home() / "Molt" / "workspace" / "repos" / "SOPHRON-CER",
        root / "repos" / "SOPHRON-CER",
    ]


_MEANING_ASSAY_SRC = _first_existing_path("MEANING_ASSAY_SRC", _candidate_meaning_assay_paths())
if _MEANING_ASSAY_SRC is not None and str(_MEANING_ASSAY_SRC) not in sys.path:
    sys.path.insert(0, str(_MEANING_ASSAY_SRC))

_ETHICS_COUNCIL_SRC = _first_existing_path("ETHICS_COUNCIL_SRC", _candidate_ethics_council_paths())
if _ETHICS_COUNCIL_SRC is not None and str(_ETHICS_COUNCIL_SRC) not in sys.path:
    sys.path.insert(0, str(_ETHICS_COUNCIL_SRC))

_CER_TELEMETRY_SRC = _first_existing_path("TRUSTWORTHY_AGENT_STACK_SRC", _candidate_tas_paths())


def _resolve_sophron_root() -> Path | None:
    env_raw = os.environ.get("SOPHRON_CER_SRC", "")
    candidates = [Path(env_raw).expanduser()] if env_raw else []
    candidates.extend(_candidate_sophron_paths())
    for candidate in candidates:
        if not candidate or not candidate.exists():
            continue
        if (candidate / "examples" / "adapter_from_cer_v01_receipts.js").exists():
            return candidate
        if (candidate / "adapters" / "cer_telemetry" / "from_v0_1_receipts.js").exists():
            return candidate
    return next((candidate for candidate in candidates if candidate and candidate.exists()), None)


_SOPHRON_CER_SRC = _resolve_sophron_root()

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

try:
    if _CER_TELEMETRY_SRC is not None and str(_CER_TELEMETRY_SRC) not in sys.path:
        sys.path.insert(0, str(_CER_TELEMETRY_SRC))
    from examples.minimal_mcp_agent.demo import run_demo as tas_run_demo
    from examples.minimal_mcp_agent.hash_utils import CANONICAL_JSON_VERSION, deterministic_hash, sign_payload
    from examples.minimal_mcp_agent.mock_ethics_council import MockEthicsCouncil, hazard_to_required_gates
    from examples.minimal_mcp_agent.sophron_ingest import validate_cer_export
except Exception:
    tas_run_demo = None
    CANONICAL_JSON_VERSION = "canonical-json-v1"
    deterministic_hash = None
    sign_payload = None
    MockEthicsCouncil = None
    hazard_to_required_gates = None
    validate_cer_export = None


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


class TrustworthyAgentStackAdapter:
    def assess(self, action: ProposedAction, council: CouncilAssessment) -> tuple[RiskState, RuntimeDisposition, dict[str, Any], AdapterProvenance]:
        if MockEthicsCouncil is None or hazard_to_required_gates is None:
            severe_hazard_count = len(council.hazards)
            if council.irreversibility_score > 0.7 or council.suspension_triggers:
                return (
                    RiskState.RED,
                    RuntimeDisposition.HALT,
                    {"risk": "RED", "evidence_chain": ["council_hazard", "suspension_trigger"]},
                    AdapterProvenance.STUB,
                )
            if severe_hazard_count >= 3 or council.contested or council.minority_reports:
                return (
                    RiskState.AMBER,
                    RuntimeDisposition.CONFIRM_HUMAN,
                    {"risk": "AMBER", "evidence_chain": ["council_hazard_density", "council_contestation"]},
                    AdapterProvenance.STUB,
                )
            return (
                RiskState.GREEN,
                RuntimeDisposition.PROCEED,
                {"risk": "GREEN", "evidence_chain": ["no blocking triggers"]},
                AdapterProvenance.STUB,
            )

        risk_level = "high" if council.irreversibility_score >= 0.7 or council.suspension_triggers else "medium"
        hazard_map = MockEthicsCouncil().evaluate_action(action.description, risk_level=risk_level)
        gates = hazard_to_required_gates(hazard_map)
        gate_records = [
            {
                "gate": gate,
                "decision": decision,
                "justification": f"Derived from TrustworthyAgentStack minimal MCP policy for {hazard_map.recommendation}",
            }
            for gate, decision in gates.items()
        ]
        if any(decision == "block" for decision in gates.values()):
            return (
                RiskState.RED,
                RuntimeDisposition.HALT,
                {
                    "risk": "RED",
                    "tas_hazard_map": hazard_map.to_payload(),
                    "gate_decisions": gate_records,
                    "evidence_chain": ["tas_gate_block"],
                },
                AdapterProvenance.REAL,
            )
        if any(decision == "escalate" for decision in gates.values()):
            return (
                RiskState.AMBER,
                RuntimeDisposition.CONFIRM_HUMAN,
                {
                    "risk": "AMBER",
                    "tas_hazard_map": hazard_map.to_payload(),
                    "gate_decisions": gate_records,
                    "evidence_chain": ["tas_gate_escalation"],
                },
                AdapterProvenance.REAL,
            )
        return (
            RiskState.GREEN,
            RuntimeDisposition.PROCEED,
            {
                "risk": "GREEN",
                "tas_hazard_map": hazard_map.to_payload(),
                "gate_decisions": gate_records,
                "evidence_chain": ["tas_gate_pass"],
            },
            AdapterProvenance.REAL,
        )


class CerSophronTelemetryAdapter(TelemetryAdapter):
    def _render_cer_metrics_receipt(self, action: ProposedAction, runtime_disposition: str) -> dict[str, Any]:
        metrics = [
            {
                "metric": "runtime_disposition_confirm_human",
                "value": 1.0 if runtime_disposition == RuntimeDisposition.CONFIRM_HUMAN.value else 0.0,
                "num": 1 if runtime_disposition == RuntimeDisposition.CONFIRM_HUMAN.value else 0,
                "den": 1,
                "low": 0.0,
                "high": 1.0,
            },
            {
                "metric": "runtime_disposition_halt",
                "value": 1.0 if runtime_disposition == RuntimeDisposition.HALT.value else 0.0,
                "num": 1 if runtime_disposition == RuntimeDisposition.HALT.value else 0,
                "den": 1,
                "low": 0.0,
                "high": 1.0,
            },
            {
                "metric": "safety_invariant_change",
                "value": 1.0 if action.context.get("change_type") == "safety_invariant" else 0.0,
                "num": 1 if action.context.get("change_type") == "safety_invariant" else 0,
                "den": 1,
                "low": 0.0,
                "high": 1.0,
            },
        ]
        manifest = {
            "run_id": action.id,
            "git_sha": sha256_hex(action.description)[:40],
            "package_version": "0.1.0",
            "config_hash": sha256_hex({"adapter": "trusted-runtime-telemetry", "schema": "cer_telemetry_receipt_v0.1"}),
            "dependency_lock_hash": sha256_hex({"python": sys.version.split()[0]}),
            "data_hash": sha256_hex({"action_id": action.id, "description": action.description, "context": action.context}),
        }
        receipt = {
            "kind": "cer_telemetry_receipt_v0.1",
            "run_id": action.id,
            "generated_at": action.timestamp.isoformat(),
            "manifest": manifest,
            "metrics": metrics,
            "source_context": {
                "description": action.description,
                "proposed_by": action.proposed_by,
                "review_kind": action.context.get("review_kind"),
                "changed_files": action.context.get("changed_files", []),
            },
        }
        receipt["receipt_sha256"] = sha256_hex(strip_receipt_timestamps(receipt))
        return receipt

    def _render_tas_export_lines(self, action: ProposedAction, runtime_disposition: str) -> list[str]:
        if deterministic_hash is None or sign_payload is None:
            raise RuntimeError("TrustworthyAgentStack hashing helpers unavailable")
        records = []
        run_payload = {
            "run_id": action.id,
            "started_at": action.timestamp.isoformat(),
            "agent_name": action.proposed_by,
            "channel": action.context.get("review_kind", "trusted_runtime"),
        }
        gate_payload = {
            "gate_check_id": f"gc_{action.id}",
            "step_id": action.id,
            "gate": "consent_traceability",
            "decision": "escalate" if runtime_disposition == RuntimeDisposition.CONFIRM_HUMAN.value else "pass",
            "justification": f"Runtime disposition derived by TrustedRuntime L2 bridge: {runtime_disposition}",
            "confidence": 0.9,
            "evidence_ref": "trusted_runtime:l2",
            "created_at": action.timestamp.isoformat(),
        }
        external_action_payload = {
            "external_action_id": f"act_{action.id}",
            "step_id": action.id,
            "action": "pr_review",
            "target": action.context.get("repo", "local_repo"),
            "status": "blocked" if runtime_disposition in {RuntimeDisposition.CONFIRM_HUMAN.value, RuntimeDisposition.HALT.value} else "simulated",
            "created_at": action.timestamp.isoformat(),
        }
        for record_type, payload in (("run", run_payload), ("gate_check", gate_payload), ("external_action", external_action_payload)):
            envelope = {
                "contract_version": "0.1",
                "schema_version": "0.1",
                "canonical_json_version": CANONICAL_JSON_VERSION,
                "export_timestamp": action.timestamp.isoformat(),
                "record_type": record_type,
                "run_id": action.id,
                "provenance_hash": deterministic_hash(payload),
                "signature": sign_payload(payload),
                "signature_algorithm": "hmac-sha256",
                "signing_key_id": "demo-hmac-key-v1",
                "payload": payload,
            }
            records.append(json.dumps(envelope, sort_keys=True, ensure_ascii=False))
        return records

    def _run_sophron_adapter(self, receipt_path: Path, output_dir: Path) -> tuple[dict[str, Any], str]:
        if _SOPHRON_CER_SRC is None:
            raise FileNotFoundError("SOPHRON-CER source path unavailable")
        adapter_script = _SOPHRON_CER_SRC / "examples" / "adapter_from_cer_v01_receipts.js"
        output_path = output_dir / "sophron_safety_report.json"
        completed = subprocess.run(
            [
                "node",
                str(adapter_script),
                "--receipts-dir",
                str(receipt_path.parent),
                "--out",
                str(output_path),
            ],
            cwd=str(_SOPHRON_CER_SRC),
            capture_output=True,
            text=True,
            check=True,
        )
        report = json.loads(output_path.read_text(encoding="utf-8"))
        return report, completed.stdout.strip()

    def collect(self, action: ProposedAction, runtime_disposition: str) -> CERRecordBundle:
        if validate_cer_export is None or deterministic_hash is None or sign_payload is None or _CER_TELEMETRY_SRC is None:
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
                sophron_validation={"passed": False, "details": "CER/TAS unavailable, stubbed telemetry used"},
                confidence_notes=["Stubbed CER/SOPHRON output, replace with real adapter"],
                adapter_provenance=AdapterProvenance.STUB,
                receipt=ReceiptRef(sha256=sha256_hex(payload), schema_version=ReceiptSchemaVersion.V1_0_0),
            )

        cer_metrics_receipt = self._render_cer_metrics_receipt(action, runtime_disposition)
        with tempfile.TemporaryDirectory(prefix="trusted-runtime-telemetry-") as temp_dir_raw:
            temp_dir = Path(temp_dir_raw)
            tas_dir = temp_dir / "tas"
            tas_dir.mkdir(parents=True, exist_ok=True)
            tas_export_path = tas_dir / f"{action.id}.jsonl"
            tas_export_path.write_text("\n".join(self._render_tas_export_lines(action, runtime_disposition)) + "\n", encoding="utf-8")

            receipts_dir = temp_dir / "receipts"
            receipts_dir.mkdir(parents=True, exist_ok=True)
            receipt_path = receipts_dir / f"{action.id}.json"
            receipt_path.write_text(json.dumps(cer_metrics_receipt, sort_keys=True, indent=2), encoding="utf-8")

            sophron_report: dict[str, Any] = {}
            sophron_stdout = ""
            adapter_provenance = AdapterProvenance.REAL
            confidence_notes = [
                "Real telemetry path used TrustworthyAgentStack-shaped CER export plus SOPHRON-CER receipt ingestion"
            ]

            try:
                sophron_report, sophron_stdout = self._run_sophron_adapter(receipt_path, temp_dir)
            except Exception as exc:
                adapter_provenance = AdapterProvenance.STUB
                confidence_notes.append(
                    f"SOPHRON adapter execution failed ({type(exc).__name__}), falling back to TAS-local validation"
                )

            tas_validation = validate_cer_export(str(tas_export_path))
            state_vectors = [
                {"t": 0, "state": "proposal_received"},
                {"t": 1, "state": runtime_disposition.lower()},
                {"t": 2, "state": "telemetry_receipt_emitted"},
            ]
            invariants_checked = [
                {
                    "invariant": violation.get("invariant", "tas_local_contract"),
                    "status": "FAILED",
                    "message": violation.get("message", violation),
                }
                for violation in tas_validation.get("violations", [])
            ]
            if not invariants_checked:
                invariants_checked.append({"invariant": "tas_local_contract", "status": "PASSED"})

            provenance_hashes = [
                cer_metrics_receipt["receipt_sha256"],
                deterministic_hash(cer_metrics_receipt["manifest"]),
                sign_payload(cer_metrics_receipt["manifest"]),
            ]

            sophron_report_valid = bool(sophron_report) and (
                sophron_report.get("ok") is True
                or sophron_report.get("kind") == "sophron_alignment_report_v0"
                or bool(sophron_report.get("report"))
            )
            sophron_validation = {
                "passed": sophron_report_valid,
                "tas_local_validation": tas_validation,
                "sophron_report": strip_receipt_timestamps(sophron_report),
                "sophron_stdout": "",
            }
            sophron_validation_for_receipt = strip_receipt_timestamps(
                {
                    "passed": sophron_report_valid,
                    "tas_local_validation": tas_validation,
                    "sophron_report": sophron_report,
                }
            )

            if not sophron_validation["passed"]:
                confidence_notes.append("SOPHRON-CER report unavailable or incomplete; only TAS-local contract validation succeeded")
                adapter_provenance = AdapterProvenance.STUB

            bundle_payload = strip_receipt_timestamps(
                {
                    "cer_receipt": cer_metrics_receipt,
                    "state_vectors": state_vectors,
                    "invariants_checked": invariants_checked,
                    "provenance_hashes": provenance_hashes,
                    "sophron_validation": sophron_validation_for_receipt,
                }
            )
            return CERRecordBundle(
                execution_id=action.id,
                state_vectors=state_vectors,
                invariants_checked=invariants_checked,
                provenance_hashes=provenance_hashes,
                sophron_validation=sophron_validation,
                confidence_notes=confidence_notes,
                adapter_provenance=adapter_provenance,
                receipt=ReceiptRef(
                    sha256=sha256_hex(bundle_payload),
                    schema_version=ReceiptSchemaVersion.V1_0_0,
                    path="cer_telemetry://receipt_v0_1",
                ),
            )


def default_adapters() -> AdapterSet:
    return AdapterSet(
        hazard=EthicsCouncilAdapter(),
        warrant=MeaningAssayAdapter(),
        telemetry=CerSophronTelemetryAdapter(),
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


def _merge_formation_hazards(council: CouncilAssessment, action: ProposedAction) -> CouncilAssessment:
    report = assess_formation_hazard(action.description, action.context)
    if not report.is_formation_event:
        return council
    merged_hazards = list(council.hazards) + [h for h in report.hazards if h not in council.hazards]
    merged_faults = list(council.fault_lines) + [f for f in report.fault_lines if f not in council.fault_lines]
    notes = list(council.confidence_notes) + [f"formation lens: {report.rationale}"]
    return council.model_copy(
        update={
            "hazards": merged_hazards,
            "fault_lines": merged_faults,
            "confidence_notes": notes,
        }
    )


def assemble_execution_decision(action: ProposedAction, adapters: AdapterSet | None = None) -> ExecutionDecision:
    adapters = adapters or default_adapters()

    council = adapters.hazard.assess(action)
    council = _merge_formation_hazards(council, action)
    tas_adapter = TrustworthyAgentStackAdapter()
    risk_state, runtime_disposition, vita_state, l2_provenance = tas_adapter.assess(action, council)
    warrant = adapters.warrant.assess(action)
    cer_bundle = adapters.telemetry.collect(action, runtime_disposition.value)

    adapter_provenance = {
        "council": council.adapter_provenance,
        "warrant": warrant.adapter_provenance,
        "cer_bundle": cer_bundle.adapter_provenance,
        "tas": l2_provenance,
    }

    reconciliation_preview = _build_reconciliation(action, runtime_disposition, warrant)
    runtime_disposition, guard_note = guard_runtime_disposition(
        runtime_disposition,
        adapter_provenance,
        warranted_action=reconciliation_preview.warranted_action if reconciliation_preview is not None else None,
        reconciliation_alignment=reconciliation_preview.alignment if reconciliation_preview is not None else None,
    )
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
    if any(provenance is not AdapterProvenance.REAL for key, provenance in adapter_provenance.items() if key in {"council", "warrant", "cer_bundle"}):
        unresolved_questions.append("One or more required layers remain stubbed or unavailable; decision should not be treated as fully independent")
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
        "tas": process_provenance_record(
            adapter_name="TrustworthyAgentStackAdapter",
            adapter_provenance=l2_provenance,
            adapter_version="0.1-local",
            adapter_path=str(_CER_TELEMETRY_SRC) if _CER_TELEMETRY_SRC else None,
            source_payload=strip_receipt_timestamps(vita_state),
        ),
        "cer_bundle": process_provenance_record(
            adapter_name="CerSophronTelemetryAdapter",
            adapter_provenance=cer_bundle.adapter_provenance,
            adapter_version="0.1-local",
            adapter_path=str(_SOPHRON_CER_SRC) if _SOPHRON_CER_SRC else str(_CER_TELEMETRY_SRC) if _CER_TELEMETRY_SRC else None,
            source_payload=strip_receipt_timestamps(cer_bundle.model_dump(mode="json")),
        ),
    }

    hazard_profile_obj = build_hazard_profile(tuple(council.hazards))
    hazard_profile = {
        "families_present": list(hazard_profile_obj.families_present),
        "max_initial_level": hazard_profile_obj.max_initial_level.name,
        "max_residual_level": hazard_profile_obj.max_residual_level.name,
        "unclassified_count": hazard_profile_obj.unclassified_count,
        "hazards": [
            {
                "family": hazard.family.value,
                "raw_label": hazard.raw_label,
                "initial_level": hazard.initial_level.name,
                "residual_level": hazard.residual_level.name,
            }
            for hazard in hazard_profile_obj.hazards
        ],
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
            "hazard_profile": hazard_profile,
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
        hazard_profile=hazard_profile,
        overall_receipt=ReceiptRef(sha256=sha256_hex(master_payload), schema_version=ReceiptSchemaVersion.V1_0_0),
    )
