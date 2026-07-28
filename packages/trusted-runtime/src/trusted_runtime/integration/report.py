from __future__ import annotations

from trusted_runtime.export import compact_verifier_provenance_summary
from trusted_runtime.exact_approval import exact_approval_commit_governance_state, exact_approval_input_preference_note, exact_approval_target_requirements
from trusted_runtime.l4_status import l4_status_interpretation
from trusted_runtime.shared.models import ExecutionDecision


def _render_integration_mode_section(lines: list[str], decision: ExecutionDecision) -> None:
    lines.extend(["", "## Integration Mode (Computed)"])
    if decision.integration_mode_report is None:
        lines.append("- overall mode: `(not computed / unavailable)`")
        return

    mode = decision.integration_mode_report
    lines.append(f"- overall mode: `{mode.mode.value}`")
    for name, comp in mode.components.items():
        if comp.behavior_real:
            status = "REAL"
        elif comp.path_real or comp.import_real:
            status = "PARTIAL"
        else:
            status = "STUB/UNAVAILABLE"
        lines.append(f"- {name}: `{status}` (import_real=`{comp.import_real}`, path_real=`{comp.path_real}`, behavior_real=`{comp.behavior_real}`)")


def render_markdown_report(decision: ExecutionDecision) -> str:
    warrant_line = "unavailable"
    soph = decision.cer_bundle.sophron_validation
    cer_enrichment = getattr(decision.cer_bundle, "cer_enrichment", None)

    soph_interpretation = l4_status_interpretation(soph.validation_status)
    cer_evaluated_at = getattr(cer_enrichment, "evaluated_at", None)
    cer_profile_hash = getattr(cer_enrichment, "profile_hash", None)
    cer_known_message_set_hash = getattr(cer_enrichment, "known_message_set_hash", None)
    cer_signature_verifier_identity = getattr(cer_enrichment, "signature_verifier_identity", None)
    cer_verifier_hash = getattr(cer_enrichment, "verifier_hash", None)
    cer_resolver_config_hash = getattr(cer_enrichment, "resolver_config_hash", None)
    cer_authority_state_digest = getattr(cer_enrichment, "authority_state_digest", None)
    if decision.warrant is not None:
        warrant_line = (
            f"{decision.normative_summary.value} "
            f"(significance={decision.warrant.significance}, warrant={decision.warrant.warrant})"
        )

    verifier_summary = compact_verifier_provenance_summary(decision)
    attest_bridge = decision.vita_state.get("attest_bridge", {})
    exact_approval_commit_preview = attest_bridge.get("exact_approval_commit_preview") or {}
    exact_approval_commit_artifact = attest_bridge.get("exact_approval_commit_artifact") or {}
    commit_governance_state = exact_approval_commit_governance_state(exact_approval_commit_artifact)
    target_requirements = exact_approval_target_requirements(attest_bridge.get("exact_approval_scope"))
    input_preference = exact_approval_input_preference_note(attest_bridge.get("typed_approval_lifted_from_legacy", False))

    lines = [
        f"# Decision Report: {decision.action_id}",
        "",
        "## Runtime outcome",
        f"- disposition: `{decision.runtime_disposition.value}`",
        f"- risk state: `{decision.risk_state.value}`",
        f"- integrity: `{decision.decision_integrity.value}`",
        f"- verifier provenance status: `{verifier_summary['status_line']}`",
        "",
        "## Normative summary",
        f"- result: {warrant_line}",
        f"- contested: `{decision.contested}`",
        "",
        "## Council hazards",
    ]
    lines.extend([f"- {item}" for item in decision.council.hazards] or ["- none"])
    lines.extend([
        "",
        "## Suspension triggers",
    ])
    lines.extend([f"- {item}" for item in decision.council.suspension_triggers] or ["- none"])
    lines.extend([
        "",
        "## Unresolved questions",
    ])
    lines.extend([f"- {item}" for item in decision.unresolved_questions] or ["- none"])
    _render_integration_mode_section(lines, decision)

    lines.extend([
        "",
        "## Adapter provenance",
        f"- council: `{decision.adapter_provenance.get('council', 'UNAVAILABLE')}`",
        f"- warrant: `{decision.adapter_provenance.get('warrant', 'UNAVAILABLE')}`",
        f"- tas: `{decision.adapter_provenance.get('tas', 'UNAVAILABLE')}`",
        f"- cer bundle: `{decision.adapter_provenance.get('cer_bundle', 'UNAVAILABLE')}`",
        "",
        "## Independence and correlation",
        f"- independently corroborated: `{decision.independently_corroborated}`",
        f"- self-attested evidence only: `{decision.self_attested_evidence_only}`",
        f"- certification-grade corroboration: `{decision.correlation_report.get('certification_grade_corroboration', False)}`",
        f"- weakest detector independence: `{decision.correlation_report.get('weakest_detector_independence', 'unknown')}`",
        "",
        "## Reconciliation",
        f"- alignment: `{decision.reconciliation.alignment if decision.reconciliation else 'n/a'}`",
        f"- rationale: {decision.reconciliation.rationale if decision.reconciliation else 'n/a'}",
        "",
        "## Process provenance",
        f"- council adapter: `{decision.process_provenance.get('council', {}).get('record_sha256', 'n/a')}`",
        f"- warrant adapter: `{decision.process_provenance.get('warrant', {}).get('record_sha256', 'n/a')}`",
        f"- cer adapter: `{decision.process_provenance.get('cer_bundle', {}).get('record_sha256', 'n/a')}`",
        f"- attest bridge: `{decision.process_provenance.get('attest_bridge', {}).get('record_sha256', 'n/a')}`",
        f"- exact approval commit artifact: `{decision.process_provenance.get('exact_approval_commit_artifact', {}).get('record_sha256', 'n/a')}`",
        "",
        "## Attest bridge",
        f"- enabled: `{attest_bridge.get('enabled', False)}`",
        f"- ingress frame: `{attest_bridge.get('ingress_frame', 'n/a')}`",
        f"- exact approval identity: `{attest_bridge.get('exact_approval_identity', 'n/a')}`",
        f"- exact approval scope: `{attest_bridge.get('exact_approval_scope', 'n/a')}`",
        f"- idempotency key: `{attest_bridge.get('exact_approval_binding', {}).get('idempotency_key', 'n/a')}`",
        f"- typed approval lifted from legacy: `{attest_bridge.get('typed_approval_lifted_from_legacy', False)}`",
        f"- input preference: {input_preference}",
        f"- exact approval source digest: `{attest_bridge.get('exact_approval_binding', {}).get('source_digest', 'n/a')}`",
        f"- exact approval connector: `{attest_bridge.get('exact_approval_binding', {}).get('connector', 'n/a')}`",
        f"- exact approval destination: `{attest_bridge.get('exact_approval_binding', {}).get('destination', 'n/a')}`",
        f"- exact approval arguments: `{attest_bridge.get('exact_approval_binding', {}).get('arguments', 'n/a')}`",
        f"- target requires connector: `{target_requirements['requires_connector']}`",
        f"- target requires destination: `{target_requirements['requires_destination']}`",
        f"- target requires arguments: `{target_requirements['requires_arguments']}`",
        f"- idempotency duplicate detected: `{decision.vita_state.get('idempotency', {}).get('duplicate_detected', False)}`",
        f"- idempotency enforcement: `{decision.vita_state.get('idempotency', {}).get('enforcement', 'none')}`",
        "- idempotency posture: process-local / ephemeral",
        "- idempotency proof note: prevents duplicate consequential intent reuse only within the current runtime process",
        f"- decision effect: `{attest_bridge.get('verification', {}).get('attest_decision_effect', 'n/a')}`",
        f"- profile: `{attest_bridge.get('verification', {}).get('attest_profile_id', 'n/a')}`",
        f"- grounds resolver: `{attest_bridge.get('verification', {}).get('attest_grounds_resolver_name', 'n/a')}`",
        f"- authority resolver: `{attest_bridge.get('verification', {}).get('attest_authority_resolver_name', 'n/a')}`",
        f"- signature verifier: `{attest_bridge.get('verification', {}).get('attest_signature_verifier_name', 'n/a')}`",
        f"- known message refs: `{attest_bridge.get('resolver_inputs', {}).get('known_message_ref_count', 0)}`",
        f"- known authority refs: `{attest_bridge.get('resolver_inputs', {}).get('known_authority_ref_count', 0)}`",
        f"- authority grants: `{len(attest_bridge.get('resolver_inputs', {}).get('authority_grant_keys', []))}`",
        "",
        "### Exact approval commit preview",
        f"- preview frame: `{exact_approval_commit_preview.get('frame', 'n/a')}`",
        f"- preview action scope: `{exact_approval_commit_preview.get('action_scope', 'n/a')}`",
        f"- preview binding receipt: `{exact_approval_commit_preview.get('binding_receipt_sha256', 'n/a')}`",
        f"- preview source digest: `{exact_approval_commit_preview.get('source_digest', 'n/a')}`",
        f"- preview idempotency key: `{exact_approval_commit_preview.get('idempotency_key', 'n/a')}`",
        f"- preview connector: `{exact_approval_commit_preview.get('connector', 'n/a')}`",
        f"- preview destination: `{exact_approval_commit_preview.get('destination', 'n/a')}`",
        f"- preview arguments: `{exact_approval_commit_preview.get('arguments', 'n/a')}`",
        f"- preview action digest: `{exact_approval_commit_preview.get('action_digest', 'n/a')}`",
        f"- preview receipt: `{exact_approval_commit_preview.get('receipt_sha256', 'n/a')}`",
        "",
        "### Exact approval commit artifact",
        f"- artifact emission state: `{exact_approval_commit_artifact.get('emission_state', 'n/a')}`",
        f"- artifact governance state: `{commit_governance_state}`",
        f"- artifact emitted: `{exact_approval_commit_artifact.get('emitted', 'n/a')}`",
        f"- artifact runtime disposition: `{exact_approval_commit_artifact.get('runtime_disposition', 'n/a')}`",
        f"- artifact source digest: `{exact_approval_commit_artifact.get('source_digest', 'n/a')}`",
        f"- artifact idempotency key: `{exact_approval_commit_artifact.get('idempotency_key', 'n/a')}`",
        f"- artifact connector: `{exact_approval_commit_artifact.get('connector', 'n/a')}`",
        f"- artifact destination: `{exact_approval_commit_artifact.get('destination', 'n/a')}`",
        f"- artifact arguments: `{exact_approval_commit_artifact.get('arguments', 'n/a')}`",
        f"- artifact action digest: `{exact_approval_commit_artifact.get('action_digest', 'n/a')}`",
        f"- artifact receipt: `{exact_approval_commit_artifact.get('receipt_sha256', 'n/a')}`",
        "",
        "### CER verifier provenance",
        f"- evaluated at: `{cer_evaluated_at.isoformat() if cer_evaluated_at else 'n/a'}`",
        f"- profile hash: `{cer_profile_hash or 'n/a'}`",
        f"- known message set hash: `{cer_known_message_set_hash or 'n/a'}`",
        f"- signature verifier identity: `{cer_signature_verifier_identity or 'n/a'}`",
        f"- verifier hash: `{cer_verifier_hash or 'n/a'}`",
        f"- resolver config hash: `{cer_resolver_config_hash or 'n/a'}`",
        f"- authority state digest: `{cer_authority_state_digest or 'n/a'}`",
        f"- exact approval identity: `{getattr(cer_enrichment, 'exact_approval_identity', None) or 'n/a'}`",
        f"- exact approval scope: `{getattr(cer_enrichment, 'exact_approval_scope', None) or 'n/a'}`",
        "",
        "## L2 closure",
        f"- enforcement maturity: `{decision.vita_state.get('tas_closure', {}).get('enforcement_maturity', 'n/a')}`",
        f"- closure complete: `{decision.vita_state.get('tas_closure', {}).get('closure_bar', {}).get('closure_complete', False)}`",
        f"- closure version: `{decision.vita_state.get('tas_closure', {}).get('closure_bar', {}).get('closure_bar_version', 'n/a')}`",
        f"- closure missing: `{', '.join(decision.vita_state.get('tas_closure', {}).get('closure_bar', {}).get('closure_missing', [])) or 'none'}`",
        f"- trace source: `{decision.vita_state.get('tas_closure', {}).get('closure_bar', {}).get('enforcement_trace', {}).get('source', 'n/a')}`",
        f"- trace checkpoints: `{', '.join(decision.vita_state.get('tas_closure', {}).get('closure_bar', {}).get('enforcement_trace', {}).get('checkpoints', [])) or 'n/a'}`",
        "",
        "## L4 evidence",
        "### SOPHRON Validation",
        f"- Status: **{soph.validation_status}**",
        f"- Interpretation: `{soph_interpretation}`",
        f"- Closure Summary: `{soph.closure_summary}`",
        f"- Receipt Linkage: `{'Yes' if soph.receipt_linkage else 'No'}`",
        f"- TAS Referenced: `{'Yes' if soph.tas_closure_referenced else 'No'}`",
        f"- Signal Tiers: `{len(soph.signal_tiers)} extracted`",
        f"- Degradation: `{soph.degradation_reason or 'n/a'}`",
        f"- Validation Closure: `{soph.l4_closure.get('closure_complete', False)}`",
        f"- Closure Version: `{soph.l4_closure.get('closure_bar_version', 'n/a')}`",
        f"- Closure Missing: `{', '.join(soph.l4_closure.get('closure_missing', [])) or 'none'}`",
        f"- TAS-local only: `{soph.l4_closure.get('reporting_axes', {}).get('tas_local_only', False)}`",
        f"- SOPHRON validated: `{soph.l4_closure.get('reporting_axes', {}).get('sophron_validated', False)}`",
        f"- Adapter failed: `{soph.l4_closure.get('reporting_axes', {}).get('adapter_failed', False)}`",
        "",
        "## Receipts",
        f"- council: `{decision.council.receipt.sha256}`",
        f"- warrant: `{decision.warrant.receipt.sha256 if decision.warrant else 'n/a'}`",
        f"- cer bundle: `{decision.cer_bundle.receipt.sha256}`",
        f"- overall: `{decision.overall_receipt.sha256}`",
        "",
    ])
    return "\n".join(lines)
