from __future__ import annotations

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
    if decision.warrant is not None:
        warrant_line = (
            f"{decision.normative_summary.value} "
            f"(significance={decision.warrant.significance}, warrant={decision.warrant.warrant})"
        )

    lines = [
        f"# Decision Report: {decision.action_id}",
        "",
        "## Runtime outcome",
        f"- disposition: `{decision.runtime_disposition.value}`",
        f"- risk state: `{decision.risk_state.value}`",
        f"- integrity: `{decision.decision_integrity.value}`",
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
        "",
        "## Attest bridge",
        f"- enabled: `{decision.vita_state.get('attest_bridge', {}).get('enabled', False)}`",
        f"- ingress frame: `{decision.vita_state.get('attest_bridge', {}).get('ingress_frame', 'n/a')}`",
        f"- decision effect: `{decision.vita_state.get('attest_bridge', {}).get('verification', {}).get('attest_decision_effect', 'n/a')}`",
        f"- profile: `{decision.vita_state.get('attest_bridge', {}).get('verification', {}).get('attest_profile_id', 'n/a')}`",
        f"- grounds resolver: `{decision.vita_state.get('attest_bridge', {}).get('verification', {}).get('attest_grounds_resolver_name', 'n/a')}`",
        f"- authority resolver: `{decision.vita_state.get('attest_bridge', {}).get('verification', {}).get('attest_authority_resolver_name', 'n/a')}`",
        f"- signature verifier: `{decision.vita_state.get('attest_bridge', {}).get('verification', {}).get('attest_signature_verifier_name', 'n/a')}`",
        f"- known message refs: `{decision.vita_state.get('attest_bridge', {}).get('resolver_inputs', {}).get('known_message_ref_count', 0)}`",
        f"- known authority refs: `{decision.vita_state.get('attest_bridge', {}).get('resolver_inputs', {}).get('known_authority_ref_count', 0)}`",
        f"- authority grants: `{len(decision.vita_state.get('attest_bridge', {}).get('resolver_inputs', {}).get('authority_grant_keys', []))}`",
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
