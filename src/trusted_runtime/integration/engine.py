from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

from trusted_runtime.config import detect_integration_mode, load_integration_paths
from trusted_runtime.integration.adapters import AdapterSet, HazardAdapter, TelemetryAdapter, WarrantAdapter
from trusted_runtime.integration.attest_bridge import AttestBridge, AttestResolverInputs
from trusted_runtime.integration.formation import assess_formation_hazard
from trusted_runtime.integration.hazard_taxonomy import build_hazard_profile
from trusted_runtime.integration.integrity import classify_decision_integrity
from trusted_runtime.integration.l2_closure import evaluate_l2_closure
from trusted_runtime.integration.l4_closure import evaluate_l4_closure
from trusted_runtime.integration.l4_evidence import build_sophron_validation_envelope
from trusted_runtime.integration.policy import guard_runtime_disposition
from trusted_runtime.shared.credal import clamp_to_status
from trusted_runtime.shared.lineage import LineageDescriptor, correlation_report, weakest_independence_for_credal
from trusted_runtime.integration.provenance import process_provenance_record
from trusted_runtime.integration.translation import derive_meaning_case
from trusted_runtime.integration.sophron_tripwire_bridge import tripwires_from_sophron_validation
from trusted_runtime.shared.enums import (
    AdapterProvenance,
    DecisionIntegrity,
    NormativeSummary,
    ReceiptSchemaVersion,
    RiskState,
    RuntimeDisposition,
    TripValidationStatus,
)
from trusted_runtime.shared.models import (
    CERFragmentEnrichment,
    CERRecordBundle,
    CouncilAssessment,
    CoverageRecord,
    EvidenceRecord,
    ExecutionDecision,
    ProposedAction,
    ReceiptRef,
    ReconciliationRecord,
    ReviewabilityProfile,
    TripwireRecord,
    WarrantAssay,
)
from trusted_runtime.shared.receipts import sha256_hex, strip_receipt_timestamps


DEFAULT_ADAPTER_LINEAGES = {
    "council": LineageDescriptor(
        author_id="ladyelinor",
        org_id="local",
        framework_lineage="trustedruntime-l1",
        source_lineage="ethics-council-local",
        operator_id="ladyelinor",
    ),
    "warrant": LineageDescriptor(
        author_id="ladyelinor",
        org_id="local",
        framework_lineage="trustedruntime-l3",
        source_lineage="meaning-assay-local",
        operator_id="ladyelinor",
    ),
}


_INTEGRATION_PATHS = load_integration_paths()

_MEANING_ASSAY_SRC = _INTEGRATION_PATHS.meaning_assay_src
if _MEANING_ASSAY_SRC is not None and str(_MEANING_ASSAY_SRC) not in sys.path:
    sys.path.insert(0, str(_MEANING_ASSAY_SRC))

_ETHICS_COUNCIL_SRC = _INTEGRATION_PATHS.ethics_council_src
if _ETHICS_COUNCIL_SRC is not None and str(_ETHICS_COUNCIL_SRC) not in sys.path:
    sys.path.insert(0, str(_ETHICS_COUNCIL_SRC))

_CER_TELEMETRY_SRC = _INTEGRATION_PATHS.trustworthy_agent_stack_src
_SOPHRON_CER_SRC = _INTEGRATION_PATHS.sophron_cer_src
_ATTEST_AGENT_CONLANG_SRC = _INTEGRATION_PATHS.attest_agent_conlang_src

_ATTEST_BRIDGE = AttestBridge(attest_root=_ATTEST_AGENT_CONLANG_SRC)

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
    from examples.minimal_mcp_agent.hash_utils import CANONICAL_JSON_VERSION, deterministic_hash, sign_payload
    from examples.minimal_mcp_agent.mock_ethics_council import MockEthicsCouncil, hazard_to_required_gates
    from examples.minimal_mcp_agent.sophron_ingest import validate_cer_export
    from scripts.route_task import classify_task as tas_classify_task
except Exception:
    CANONICAL_JSON_VERSION = "canonical-json-v1"
    deterministic_hash = None
    sign_payload = None
    MockEthicsCouncil = None
    hazard_to_required_gates = None
    validate_cer_export = None
    tas_classify_task = None


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
        translation = derive_meaning_case(action.description, action.context)
        case_key = translation["case_key"]
        translation_notes = list(translation.get("notes", []))
        pair_contrasts = {
            "source_case": case_key,
            "translation_notes": translation_notes,
            "translation_fit_quality": translation.get("fit_quality"),
            "translation_fit_reason": translation.get("fit_reason"),
            "translation_matched_signals": list(translation.get("matched_signals", [])),
            "translation_alternative_candidates": list(translation.get("alternative_candidates", [])),
            "fallback_used": bool(translation.get("fallback_used", False)),
        }
        if (
            analyze is not None
            and meaning_assay_receipt is not None
            and get_meaning_case is not None
            and case_key
        ):
            try:
                case = get_meaning_case(case_key)
            except KeyError:
                pair_contrasts["translation_resolution"] = "provisional_unbacked_case_family"
                payload = {
                    "layer": "meaning_assay_provisional",
                    "decision_id": action.id,
                    "case_key": case_key,
                    "translation": translation,
                    "normative_summary": NormativeSummary.UNDETERMINED.value,
                }
                return WarrantAssay(
                    decision_id=action.id,
                    significance=0.5,
                    warrant=0.0,
                    normative_summary=NormativeSummary.UNDETERMINED,
                    failure_modes=["provisional case family is not yet backed by a local meaning-assay worked case"],
                    pair_contrasts=pair_contrasts,
                    confidence_notes=[f"Translation mapped to provisional case family '{case_key}', but no local meaning-assay case exists yet"],
                    unresolved_questions=[f"Author a local meaning-assay case for '{case_key}' before treating this as a real warrant analysis"],
                    contested=True,
                    adapter_provenance=AdapterProvenance.PARTIAL,
                    receipt=ReceiptRef(sha256=sha256_hex(payload), schema_version=ReceiptSchemaVersion.V1_0_0),
                )
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
                pair_contrasts=pair_contrasts,
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
            "translation": translation,
        }
        return WarrantAssay(
            decision_id=action.id,
            significance=payload["significance"],
            warrant=payload["warrant"],
            normative_summary=NormativeSummary.DANGEROUS,
            failure_modes=["warrant gap in safety-critical modification"],
            pair_contrasts=pair_contrasts,
            confidence_notes=["meaning-assay unavailable or unmapped, stubbed warrant output used"],
            unresolved_questions=["Does the act preserve human review at the right boundary?"],
            contested=True,
            adapter_provenance=AdapterProvenance.STUB,
            receipt=ReceiptRef(sha256=sha256_hex(payload), schema_version=ReceiptSchemaVersion.V1_0_0),
        )


class TrustworthyAgentStackAdapter:
    def assess(self, action: ProposedAction, council: CouncilAssessment) -> tuple[RiskState, RuntimeDisposition, dict[str, Any], AdapterProvenance]:
        severe_hazard_count = len(council.hazards)
        if MockEthicsCouncil is None or hazard_to_required_gates is None:
            if council.irreversibility_score > 0.7 or council.suspension_triggers:
                return (
                    RiskState.RED,
                    RuntimeDisposition.HALT,
                    {
                        "risk": "RED",
                        "evidence_chain": ["council_hazard", "suspension_trigger"],
                        "enforcement_maturity": "stub",
                        "closure_bar": evaluate_l2_closure(
                            has_live_stack=False,
                            route_name=None,
                            gate_records=[],
                            evidence_chain=["council_hazard", "suspension_trigger"],
                            risk_state="RED",
                            runtime_disposition="HALT",
                            hazard_payload=None,
                            receipt_linkage=None,
                        ),
                    },
                    AdapterProvenance.STUB,
                )
            if severe_hazard_count >= 3 or council.contested or council.minority_reports:
                return (
                    RiskState.AMBER,
                    RuntimeDisposition.CONFIRM_HUMAN,
                    {
                        "risk": "AMBER",
                        "evidence_chain": ["council_hazard_density", "council_contestation"],
                        "enforcement_maturity": "stub",
                        "closure_bar": evaluate_l2_closure(
                            has_live_stack=False,
                            route_name=None,
                            gate_records=[],
                            evidence_chain=["council_hazard_density", "council_contestation"],
                            risk_state="AMBER",
                            runtime_disposition="CONFIRM_HUMAN",
                            hazard_payload=None,
                            receipt_linkage=None,
                        ),
                    },
                    AdapterProvenance.STUB,
                )
            return (
                RiskState.GREEN,
                RuntimeDisposition.PROCEED,
                {
                    "risk": "GREEN",
                    "evidence_chain": ["no blocking triggers"],
                    "enforcement_maturity": "stub",
                    "closure_bar": evaluate_l2_closure(
                        has_live_stack=False,
                        route_name=None,
                        gate_records=[],
                        evidence_chain=["no blocking triggers"],
                        risk_state="GREEN",
                        runtime_disposition="PROCEED",
                        hazard_payload=None,
                        receipt_linkage=None,
                    ),
                },
                AdapterProvenance.STUB,
            )

        routing = tas_classify_task(action.description) if tas_classify_task is not None else None
        risk_level = "high" if council.irreversibility_score >= 0.7 or council.suspension_triggers else "medium"
        hazard_map = MockEthicsCouncil().evaluate_action(action.description, risk_level=risk_level)
        gates = hazard_to_required_gates(hazard_map)
        route_name = getattr(routing, "route", None)
        route_confidence = getattr(routing, "confidence", None)
        route_reasons = list(getattr(routing, "reasons", []) or [])

        if route_name == "never_auto_route":
            gates["task_route"] = "block"
        elif route_name == "openclaw":
            gates.setdefault("task_route", "pass")
        elif route_name == "picobot":
            gates.setdefault("task_route", "escalate")

        gate_records = [
            {
                "gate": gate,
                "decision": decision,
                "justification": f"Derived from TrustworthyAgentStack minimal MCP policy for {hazard_map.recommendation}",
            }
            for gate, decision in gates.items()
        ]
        if route_name is not None:
            for record in gate_records:
                if record["gate"] == "task_route":
                    record["justification"] = f"Derived from TrustworthyAgentStack routing rubric: {route_name} ({route_confidence})"
                    record["reasons"] = route_reasons

        hazard_payload = hazard_map.to_payload()
        red_evidence = ["tas_gate_block"]
        amber_evidence = ["tas_gate_escalation"]
        green_evidence = ["tas_gate_pass"]
        receipt_linkage = {
            "trace_id": action.id,
            "source": "trustworthy_agent_stack.runtime",
        }
        closure_bar_for_red = evaluate_l2_closure(
            has_live_stack=True,
            route_name=route_name,
            gate_records=gate_records,
            evidence_chain=red_evidence,
            risk_state="RED",
            runtime_disposition="HALT",
            hazard_payload=hazard_payload,
            receipt_linkage=receipt_linkage,
        )
        closure_bar_for_amber = evaluate_l2_closure(
            has_live_stack=True,
            route_name=route_name,
            gate_records=gate_records,
            evidence_chain=amber_evidence,
            risk_state="AMBER",
            runtime_disposition="CONFIRM_HUMAN",
            hazard_payload=hazard_payload,
            receipt_linkage=receipt_linkage,
        )
        closure_bar_for_green = evaluate_l2_closure(
            has_live_stack=True,
            route_name=route_name,
            gate_records=gate_records,
            evidence_chain=green_evidence,
            risk_state="GREEN",
            runtime_disposition="PROCEED",
            hazard_payload=hazard_payload,
            receipt_linkage=receipt_linkage,
        )
        base_state = {
            "tas_hazard_map": hazard_payload,
            "gate_decisions": gate_records,
            "task_routing": {
                "route": route_name,
                "confidence": route_confidence,
                "reasons": route_reasons,
            } if route_name is not None else None,
        }
        if any(decision == "block" for decision in gates.values()):
            return (
                RiskState.RED,
                RuntimeDisposition.HALT,
                {
                    "risk": "RED",
                    **base_state,
                    "evidence_chain": red_evidence,
                    "enforcement_maturity": "real" if closure_bar_for_red["closure_complete"] else "partial",
                    "closure_bar": closure_bar_for_red,
                },
                AdapterProvenance.REAL if closure_bar_for_red["closure_complete"] else AdapterProvenance.PARTIAL,
            )
        if any(decision == "escalate" for decision in gates.values()):
            return (
                RiskState.AMBER,
                RuntimeDisposition.CONFIRM_HUMAN,
                {
                    "risk": "AMBER",
                    **base_state,
                    "evidence_chain": amber_evidence,
                    "enforcement_maturity": "real" if closure_bar_for_amber["closure_complete"] else "partial",
                    "closure_bar": closure_bar_for_amber,
                },
                AdapterProvenance.REAL if closure_bar_for_amber["closure_complete"] else AdapterProvenance.PARTIAL,
            )
        return (
            RiskState.GREEN,
            RuntimeDisposition.PROCEED,
            {
                "risk": "GREEN",
                **base_state,
                "evidence_chain": green_evidence,
                "enforcement_maturity": "real" if closure_bar_for_green["closure_complete"] else "partial",
                "closure_bar": closure_bar_for_green,
            },
            AdapterProvenance.REAL if closure_bar_for_green["closure_complete"] else AdapterProvenance.PARTIAL,
        )


class CerSophronTelemetryAdapter(TelemetryAdapter):
    def _extract_sophron_signal_tiers(self, sophron_report: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(sophron_report, dict):
            return {}

        signal_validation = sophron_report.get("signal_validation")
        native_signals = signal_validation.get("signals") if isinstance(signal_validation, dict) else None
        if isinstance(native_signals, dict):
            normalized: dict[str, Any] = {}
            for signal_id, payload in native_signals.items():
                if not isinstance(payload, dict):
                    continue
                signal_payload = strip_receipt_timestamps(payload.get("signal_payload", {})) if isinstance(payload.get("signal_payload"), dict) else {}
                evidence_refs = payload.get("evidence_refs") if isinstance(payload.get("evidence_refs"), list) else []
                normalized[signal_id] = {
                    **strip_receipt_timestamps(payload),
                    "signal_id": signal_id,
                    "evidence_refs": [str(item) for item in evidence_refs],
                    "signal_payload": signal_payload,
                    "semantic_checks": {
                        "has_signal_id": True,
                        "allowed_tier_source": str(payload.get("tier_source", "")).strip() in {"sophron-emitted", "tr-derived"},
                        "allowed_source_layer": str(payload.get("source_layer", "")).strip() == "sophron-cer",
                        "evidence_refs_typed": all(isinstance(item, str) for item in evidence_refs),
                    },
                }
            return normalized

        report = sophron_report.get("report") if isinstance(sophron_report, dict) else None
        signals = report.get("signals") if isinstance(report, dict) else None
        if not isinstance(signals, dict):
            return {}

        extracted: dict[str, Any] = {}
        for signal_name in ("shift", "game", "decept", "corrig", "human"):
            signal_payload = signals.get(signal_name)
            if not isinstance(signal_payload, dict):
                continue
            signal_id = f"sophron.{signal_name}"
            evidence_refs = [
                str(item.get("id"))
                for item in signal_payload.get("evidence", [])
                if isinstance(item, dict) and item.get("id") is not None
            ] if isinstance(signal_payload.get("evidence"), list) else []
            extracted[signal_id] = {
                "signal_id": signal_id,
                "tier": "validated-sim",
                "tier_source": "tr-derived",
                "source_layer": "sophron-cer",
                "rationale": "Derived by TrustedRuntime from the returned SOPHRON-CER alignment report shape; current calibration evidence is treated as simulation-backed unless upstream field validation is explicitly emitted.",
                "evidence_refs": evidence_refs,
                "signal_payload": strip_receipt_timestamps(signal_payload),
                "semantic_checks": {
                    "has_signal_id": True,
                    "allowed_tier_source": True,
                    "allowed_source_layer": True,
                    "evidence_refs_typed": all(isinstance(item, str) for item in evidence_refs),
                    "payload_matches_signal": signal_name in signal_id,
                },
            }
        return extracted

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
            "action_description_digest": sha256_hex(action.description),
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
        metric_payload = {
            "metric_name": "runtime_disposition_confirm_human",
            "value": 1.0 if runtime_disposition == RuntimeDisposition.CONFIRM_HUMAN.value else 0.0,
            "step_id": action.id,
            "created_at": action.timestamp.isoformat(),
        }
        gate_payload = {
            "gate": "consent_traceability",
            "decision": "escalate" if runtime_disposition == RuntimeDisposition.CONFIRM_HUMAN.value else "pass",
            "confidence": 0.9,
            "step_id": action.id,
            "created_at": action.timestamp.isoformat(),
        }
        cohort_payload = {
            "cohort_name": "runtime_blocked_actions" if runtime_disposition in {RuntimeDisposition.CONFIRM_HUMAN.value, RuntimeDisposition.HALT.value} else "runtime_simulated_actions",
            "included_run_ids": [action.id],
            "excluded_run_ids": [],
            "overlap_count": 0,
            "created_at": action.timestamp.isoformat(),
        }
        for record_type, payload in (("metric_observation", metric_payload), ("gate_outcome", gate_payload), ("cohort_partition", cohort_payload)):
            envelope = {
                "contract_version": "0.1",
                "schema_version": "0.1",
                "canonical_json_version": CANONICAL_JSON_VERSION,
                "export_timestamp": action.timestamp.isoformat(),
                "record_type": record_type,
                "run_id": action.id,
                "provenance_hash": deterministic_hash(payload),
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

    def collect(
        self,
        action: ProposedAction,
        runtime_disposition: str,
        cer_enrichment: CERFragmentEnrichment | None = None,
    ) -> CERRecordBundle:
        cer_enrichment = cer_enrichment or CERFragmentEnrichment()
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
                sophron_validation=build_sophron_validation_envelope(
                    sophron_report_valid=False,
                    sophron_signals={},
                    tas_local_validation={},
                    sophron_report={},
                    sophron_stdout="",
                    l4_closure={},
                    degradation_reason="CER/TAS unavailable, stubbed telemetry used",
                    receipt_linkage=False,
                    tas_closure_referenced=False,
                ),
                cer_enrichment=cer_enrichment,
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
            adapter_error: str | None = None
            confidence_notes = [
                "Real telemetry path used TrustworthyAgentStack-shaped CER export plus SOPHRON-CER receipt ingestion"
            ]

            try:
                sophron_report, sophron_stdout = self._run_sophron_adapter(receipt_path, temp_dir)
            except Exception as exc:
                adapter_provenance = AdapterProvenance.STUB
                adapter_error = f"{type(exc).__name__}"
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
                    "invariant": violation.get("invariant", "tas_local_contract") if isinstance(violation, dict) else "tas_local_contract",
                    "status": "FAILED",
                    "message": violation.get("message", violation) if isinstance(violation, dict) else str(violation),
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
            sophron_signals = self._extract_sophron_signal_tiers(sophron_report)
            l4_closure = evaluate_l4_closure(
                tas_local_validation=tas_validation,
                sophron_report=sophron_report,
                sophron_report_valid=sophron_report_valid,
                provenance_hashes=provenance_hashes,
                state_vectors=state_vectors,
                invariants_checked=invariants_checked,
                adapter_error=adapter_error,
            )
            sophron_validation = build_sophron_validation_envelope(
                sophron_report_valid=sophron_report_valid,
                sophron_signals=sophron_signals,
                tas_local_validation=tas_validation,
                sophron_report=strip_receipt_timestamps(sophron_report),
                sophron_stdout="",
                l4_closure=l4_closure,
                degradation_reason=adapter_error,
                receipt_linkage=bool(provenance_hashes),
                tas_closure_referenced=True,
            )
            sophron_validation_for_receipt = strip_receipt_timestamps(sophron_validation.model_dump(mode="json"))

            if not sophron_validation.passed:
                confidence_notes.append("SOPHRON-CER report unavailable or incomplete; only TAS-local contract validation succeeded")
                adapter_provenance = AdapterProvenance.PARTIAL if tas_validation else AdapterProvenance.STUB

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
                cer_enrichment=cer_enrichment,
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

    try:
        analysis_case = get_meaning_case(source_case)
    except KeyError:
        return None
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


# Evidence classes that count as corroboration NOT originating from the actor's own
# say-so. self_attested and same-operator are both actor-supplied and do not count;
# only locally re-verified or genuinely third-party evidence does.
_INDEPENDENT_EVIDENCE_CLASSES = frozenset({"verified-local", "independent-third-party"})


def _build_evidence_records(action: ProposedAction) -> list[EvidenceRecord]:
    records: list[EvidenceRecord] = [
        EvidenceRecord(
            kind="proposed_action",
            source="proposed_action.description",
            independence_class="self_attested",
            self_attested=True,
            reviewable=True,
            notes=["Actor-supplied proposal text is evidence-of-claim, not evidence-of-fact"],
        )
    ]
    claimed = action.context.get("claimed_provenance")
    if claimed is not None:
        records.append(
            EvidenceRecord(
                kind="claimed_provenance",
                source="proposed_action.context.claimed_provenance",
                independence_class="self_attested",
                self_attested=True,
                reviewable=True,
                notes=[f"Unverified actor claim: {claimed}"],
            )
        )
    changed_files = action.context.get("changed_files")
    if changed_files:
        records.append(
            EvidenceRecord(
                kind="changed_files_manifest",
                source="proposed_action.context.changed_files",
                independence_class="same-operator",
                self_attested=False,
                reviewable=True,
                notes=["Changed-file manifest supplied in action context; requires independent verification for fact claims"],
            )
        )
    return records


def _build_reviewability_profile(action: ProposedAction) -> ReviewabilityProfile:
    rationale_chars = len(action.description or "")
    components = ["description"]
    review_surface_chars = rationale_chars

    context = action.context or {}
    if context.get("review_kind"):
        review_surface_chars += len(str(context.get("review_kind")))
        components.append("context.review_kind")
    if context.get("repo"):
        review_surface_chars += len(str(context.get("repo")))
        components.append("context.repo")
    if context.get("author"):
        review_surface_chars += len(str(context.get("author")))
        components.append("context.author")
    changed_files = context.get("changed_files") or []
    if changed_files:
        review_surface_chars += sum(len(str(item)) for item in changed_files)
        components.append("context.changed_files")
    claimed_provenance = context.get("claimed_provenance")
    if claimed_provenance is not None:
        review_surface_chars += len(str(claimed_provenance))
        components.append("context.claimed_provenance")

    review_budget_chars = 4000
    exceeded = review_surface_chars > review_budget_chars
    notes = []
    if exceeded:
        notes.append("Review surface exceeds reviewability budget; long justifications are treated as a hazard signal")
    else:
        notes.append("Review surface fits within reviewability budget")
    return ReviewabilityProfile(
        rationale_chars=rationale_chars,
        review_surface_chars=review_surface_chars,
        review_surface_components=components,
        review_budget_chars=review_budget_chars,
        within_budget=not exceeded,
        exceeded=exceeded,
        notes=notes,
    )


def _tripwire_records(
    council: CouncilAssessment,
    warrant: WarrantAssay | None,
    cer_bundle: CERRecordBundle,
    reconciliation: ReconciliationRecord | None,
    *,
    weakest_detector_independence: str | None = None,
) -> list[TripwireRecord]:
    records = [
        TripwireRecord(
            tripwire_id="tripwire.independent_corroboration",
            status=TripValidationStatus.VALIDATED,
            source_layer="trusted_runtime.policy",
            rationale="Independent corroboration guard is a live runtime policy invariant, not a heuristic detector.",
            allowed_for_blocking=True,
            allowed_for_advisory=True,
            notes=["Self-attested and same-operator evidence do not satisfy this gate."],
        ),
        TripwireRecord(
            tripwire_id="tripwire.reviewability_budget",
            status=TripValidationStatus.VALIDATED,
            source_layer="trusted_runtime.policy",
            rationale="Reviewability budget is a live runtime policy invariant over justification surface size.",
            allowed_for_blocking=True,
            allowed_for_advisory=True,
        ),
        TripwireRecord(
            tripwire_id="tripwire.ethics_council_hazard",
            status=TripValidationStatus.CALIBRATING,
            source_layer="council",
            rationale="EthicsCouncil outputs are real and structurally integrated, but the repo still describes itself as heuristic/calibrating.",
            allowed_for_blocking=False,
            allowed_for_advisory=True,
            evidence_refs=[council.receipt.sha256],
            credal=clamp_to_status(
                None,
                TripValidationStatus.CALIBRATING,
                weakest_independence=weakest_detector_independence,
            ),
        ),
        TripwireRecord(
            tripwire_id="tripwire.meaning_assay_warrant",
            status=TripValidationStatus.CALIBRATING if warrant is not None else TripValidationStatus.UNVALIDATED,
            source_layer="warrant",
            rationale="meaning-assay is real when available, but its downstream runtime gate role remains advisory rather than independently validated as a blocking detector.",
            allowed_for_blocking=False,
            allowed_for_advisory=True,
            evidence_refs=[warrant.receipt.sha256] if warrant is not None else [],
            credal=clamp_to_status(
                None,
                TripValidationStatus.CALIBRATING if warrant is not None else TripValidationStatus.UNVALIDATED,
                weakest_independence=weakest_detector_independence,
            ),
        ),
    ]
    records.extend(tripwires_from_sophron_validation(cer_bundle.sophron_validation))
    if reconciliation is not None:
        records.append(
            TripwireRecord(
                tripwire_id="tripwire.reconciliation_alignment",
                status=TripValidationStatus.VALIDATED,
                source_layer="trusted_runtime.reconciliation",
                rationale="Runtime policy explicitly blocks PROCEED on under-justified or over-reactive reconciliation results.",
                allowed_for_blocking=True,
                allowed_for_advisory=True,
                evidence_refs=[reconciliation.receipt.sha256] if reconciliation.receipt is not None else [],
            )
        )
    return records


def _coverage_records(
    council: CouncilAssessment,
    warrant: WarrantAssay | None,
    cer_bundle: CERRecordBundle,
    reconciliation: ReconciliationRecord | None,
    adapter_provenance: dict[str, AdapterProvenance],
) -> list[CoverageRecord]:
    coverage: list[CoverageRecord] = []
    if adapter_provenance.get("council") is AdapterProvenance.REAL:
        coverage.append(CoverageRecord(layer="council", mode="direct-real"))
    if adapter_provenance.get("tas") is AdapterProvenance.REAL:
        coverage.append(CoverageRecord(layer="tas", mode="direct-real"))
    if adapter_provenance.get("cer_bundle") is AdapterProvenance.REAL:
        coverage.append(CoverageRecord(layer="cer_bundle", mode="direct-real"))
    if warrant is not None and adapter_provenance.get("warrant") is AdapterProvenance.REAL:
        coverage.append(CoverageRecord(layer="warrant", mode="direct-real"))
    if reconciliation is not None and adapter_provenance.get("warrant") is AdapterProvenance.REAL:
        coverage.append(CoverageRecord(layer="reconciliation", mode="derived-advisory", notes=["Derived from the real warrant layer plus council/runtime mapping"]))
    if any(h.startswith("formation::") for h in council.hazards):
        coverage.append(CoverageRecord(layer="formation_lens", mode="derived-advisory", notes=["Derived additive lens layered onto council hazards"]))
    return coverage


def _attest_resolver_inputs_for_action(action: ProposedAction, evidence_records: list[EvidenceRecord]) -> AttestResolverInputs:
    context = action.context or {}

    known_message_refs: list[str] = []
    for item in context.get("attest_known_message_refs") or []:
        ref = str(item).strip()
        if ref and ref not in known_message_refs:
            known_message_refs.append(ref)

    known_authority_refs: list[str] = []
    for item in context.get("attest_known_authority_refs") or []:
        ref = str(item).strip()
        if ref and ref not in known_authority_refs:
            known_authority_refs.append(ref)

    authority_grants = context.get("attest_authority_grants") or {}
    if not isinstance(authority_grants, dict):
        authority_grants = {}

    grounds_status_overrides = context.get("attest_grounds_status_overrides") or {}
    if not isinstance(grounds_status_overrides, dict):
        grounds_status_overrides = {}

    authority_status_overrides = context.get("attest_authority_status_overrides") or {}
    if not isinstance(authority_status_overrides, dict):
        authority_status_overrides = {}

    for record in evidence_records:
        if record.source and record.source not in known_message_refs:
            known_message_refs.append(record.source)

    return AttestResolverInputs(
        known_message_refs=known_message_refs,
        known_authority_refs=known_authority_refs,
        authority_grants=authority_grants,
        grounds_status_overrides={str(k): str(v) for k, v in grounds_status_overrides.items()},
        authority_status_overrides={str(k): str(v) for k, v in authority_status_overrides.items()},
    )


def _attest_resolver_summary(resolver_inputs: AttestResolverInputs) -> dict[str, Any]:
    return {
        "known_message_ref_count": len(resolver_inputs.known_message_refs),
        "known_message_refs_preview": resolver_inputs.known_message_refs[:5],
        "known_authority_ref_count": len(resolver_inputs.known_authority_refs),
        "known_authority_refs_preview": resolver_inputs.known_authority_refs[:5],
        "authority_grant_keys": sorted(resolver_inputs.authority_grants.keys()),
        "grounds_status_override_keys": sorted(resolver_inputs.grounds_status_overrides.keys()),
        "authority_status_override_keys": sorted(resolver_inputs.authority_status_overrides.keys()),
    }


def _cer_enrichment_from_attest_verification(verification: Any) -> CERFragmentEnrichment:
    resolver_config_hash = sha256_hex(
        {
            "grounds_resolver_config_hash": verification.grounds_resolver_config_hash,
            "authority_resolver_config_hash": verification.authority_resolver_config_hash,
        }
    )
    verifier_hash = sha256_hex(
        {
            "verifier_version": verification.verifier_version,
            "signature_verifier_name": verification.signature_verifier_name,
            "signature_verifier_config_hash": verification.signature_verifier_config_hash,
        }
    )
    return CERFragmentEnrichment(
        evaluated_at=verification.evaluated_at,
        profile_hash=verification.profile_hash,
        verifier_hash=verifier_hash,
        resolver_config_hash=resolver_config_hash,
        known_message_set_hash=verification.known_message_set_hash,
        signature_verifier_identity=verification.signature_verifier_name,
        replay_nonce=None,
    )


def assemble_execution_decision(action: ProposedAction, adapters: AdapterSet | None = None) -> ExecutionDecision:
    adapters = adapters or default_adapters()

    evidence_records = _build_evidence_records(action)
    attest_resolver_inputs = _attest_resolver_inputs_for_action(action, evidence_records)
    attest_ingress_message = _ATTEST_BRIDGE.wrap_ingress_request(action)
    attest_ingress_verification = _ATTEST_BRIDGE.verify_for_runtime(
        attest_ingress_message,
        [],
        resolver_inputs=attest_resolver_inputs,
        evaluated_at=action.timestamp,
    )
    attest_receipt_fragment = _ATTEST_BRIDGE.cer_receipt_fragment(verification=attest_ingress_verification)
    attest_cer_enrichment = _cer_enrichment_from_attest_verification(attest_ingress_verification)

    reviewability = _build_reviewability_profile(action)

    council = adapters.hazard.assess(action)
    council = _merge_formation_hazards(council, action)
    council = council.model_copy(update={"evidence_records": evidence_records, "reviewability": reviewability})
    tas_adapter = TrustworthyAgentStackAdapter()
    risk_state, runtime_disposition, vita_state, l2_provenance = tas_adapter.assess(action, council)
    vita_state = {
        **vita_state,
        "attest_bridge": {
            "enabled": True,
            "real_available": _ATTEST_BRIDGE.real_available,
            "ingress_frame": attest_ingress_message.get("frame"),
            "resolver_inputs": _attest_resolver_summary(attest_resolver_inputs),
            "verification": attest_receipt_fragment,
        },
        "tas_closure": {
            "enforcement_maturity": vita_state.get("enforcement_maturity"),
            "closure_bar": vita_state.get("closure_bar"),
        },
    }
    warrant = adapters.warrant.assess(action)
    cer_bundle = adapters.telemetry.collect(
        action,
        runtime_disposition.value,
        cer_enrichment=attest_cer_enrichment,
    )

    adapter_provenance = {
        "council": council.adapter_provenance,
        "warrant": warrant.adapter_provenance,
        "cer_bundle": cer_bundle.adapter_provenance,
        "tas": l2_provenance,
    }

    local_fact_records: list[EvidenceRecord] = []
    changed_files = action.context.get("changed_files") or []
    if changed_files:
        repo_name = str(action.context.get("repo") or "")
        if repo_name in {"LadyElinor/TrustedRuntime", "TrustedRuntime", "."} and isinstance(changed_files, list):
            repo_root = Path(__file__).resolve().parents[3]
            resolved = [repo_root / str(item) for item in changed_files]
            existing = [str(path.relative_to(repo_root)) for path in resolved if path.exists()]
            missing = [str(path.relative_to(repo_root)) for path in resolved if not path.exists()]
            if existing:
                local_fact_records.append(
                    EvidenceRecord(
                        kind="changed_files_manifest_verified_local_existence",
                        source="trusted_runtime.local_validation.changed_files.repo_state",
                        independence_class="verified-local",
                        self_attested=False,
                        reviewable=True,
                        notes=[f"Local runtime verified listed files exist in repo state: {existing}"] + ([f"Missing listed files: {missing}"] if missing else []),
                    )
                )
            elif missing:
                local_fact_records.append(
                    EvidenceRecord(
                        kind="changed_files_manifest_missing_local_paths",
                        source="trusted_runtime.local_validation.changed_files.repo_state",
                        independence_class="same-operator",
                        self_attested=False,
                        reviewable=True,
                        notes=[f"Actor-supplied changed_files entries did not resolve in local repo state: {missing}"],
                    )
                )

    evidence_records = evidence_records + local_fact_records
    council = council.model_copy(update={"evidence_records": evidence_records, "reviewability": reviewability})

    self_attested_evidence_only = bool(evidence_records) and all(record.self_attested for record in evidence_records)
    independently_corroborated = any(
        record.independence_class in _INDEPENDENT_EVIDENCE_CLASSES for record in evidence_records
    )

    reconciliation_preview = _build_reconciliation(action, runtime_disposition, warrant)
    adapter_correlation = correlation_report(DEFAULT_ADAPTER_LINEAGES)
    tripwire_records = _tripwire_records(
        council,
        warrant,
        cer_bundle,
        reconciliation_preview,
        weakest_detector_independence=weakest_independence_for_credal(adapter_correlation),
    )
    runtime_disposition, guard_note = guard_runtime_disposition(
        runtime_disposition,
        adapter_provenance,
        warranted_action=reconciliation_preview.warranted_action if reconciliation_preview is not None else None,
        reconciliation_alignment=reconciliation_preview.alignment if reconciliation_preview is not None else None,
        independently_corroborated=independently_corroborated,
        reviewability_exceeded=reviewability.exceeded,
        tripwire_records=tripwire_records,
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
    if not independently_corroborated:
        unresolved_questions.append("Decision lacks independent corroboration (evidence is self-attested or same-operator only) and must not be treated as independently verified")
    if not adapter_correlation.get("certification_grade_corroboration", False):
        unresolved_questions.append("Assessors do not provide independent corroboration across distinct lineage classes and must not be treated as certification-grade confirmation")
    if reviewability.exceeded:
        unresolved_questions.append("Action rationale exceeded reviewability budget and should not be treated as fully surveyable")
    if any(record.allowed_for_blocking and record.status is not TripValidationStatus.VALIDATED for record in tripwire_records):
        unresolved_questions.append("One or more blocking tripwires are not yet validated and must not be treated as fully trustworthy blockers")
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
        "attest_bridge": process_provenance_record(
            adapter_name="AttestBridge",
            adapter_provenance=AdapterProvenance.REAL if _ATTEST_BRIDGE.real_available else AdapterProvenance.STUB,
            adapter_version="attest_ref_impl" if _ATTEST_BRIDGE.real_available else "draft-0",
            adapter_path=str(_ATTEST_AGENT_CONLANG_SRC) if _ATTEST_AGENT_CONLANG_SRC is not None else str(Path(__file__).resolve().parent / "attest_bridge.py"),
            source_payload=strip_receipt_timestamps(
                {
                    "message": attest_ingress_message,
                    "resolver_inputs": _attest_resolver_summary(attest_resolver_inputs),
                    "verification": attest_receipt_fragment,
                }
            ),
        ),
        "tas_closure": process_provenance_record(
            adapter_name="TrustworthyAgentStackClosure",
            adapter_provenance=l2_provenance,
            adapter_version="phase2-v3",
            adapter_path=str(Path(__file__).resolve().parent / "l2_closure.py"),
            source_payload=strip_receipt_timestamps(vita_state.get("tas_closure", {})),
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

    coverage_records = _coverage_records(council, warrant, cer_bundle, reconciliation, adapter_provenance)
    coverage_set = [record.layer for record in coverage_records]
    integration_mode_report = detect_integration_mode()

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
            "attest_bridge": {
                "message": attest_ingress_message,
                "resolver_inputs": _attest_resolver_summary(attest_resolver_inputs),
                "verification": attest_receipt_fragment,
            },
            "tas_closure": vita_state.get("tas_closure", {}),
            "reconciliation": reconciliation.model_dump(mode="json") if reconciliation is not None else None,
            "hazard_profile": hazard_profile,
            "evidence_records": [record.model_dump(mode="json") for record in evidence_records],
            "reviewability": reviewability.model_dump(mode="json"),
            "coverage_set": coverage_set,
            "coverage_records": [record.model_dump(mode="json") for record in coverage_records],
            "tripwire_records": [record.model_dump(mode="json") for record in tripwire_records],
            "correlation_report": adapter_correlation,
            "self_attested_evidence_only": self_attested_evidence_only,
            "independently_corroborated": independently_corroborated,
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
        evidence_records=evidence_records,
        reviewability=reviewability,
        coverage_set=coverage_set,
        coverage_records=coverage_records,
        tripwire_records=tripwire_records,
        correlation_report=adapter_correlation,
        self_attested_evidence_only=self_attested_evidence_only,
        independently_corroborated=independently_corroborated,
        integration_mode_report=integration_mode_report,
        overall_receipt=ReceiptRef(sha256=sha256_hex(master_payload), schema_version=ReceiptSchemaVersion.V1_0_0),
    )
