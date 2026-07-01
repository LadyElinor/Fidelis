from __future__ import annotations

from trusted_runtime.shared.models import ExecutionDecision


def render_markdown_report(decision: ExecutionDecision) -> str:
    warrant_line = "unavailable"
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
        "",
        "## Receipts",
        f"- council: `{decision.council.receipt.sha256}`",
        f"- warrant: `{decision.warrant.receipt.sha256 if decision.warrant else 'n/a'}`",
        f"- cer bundle: `{decision.cer_bundle.receipt.sha256}`",
        f"- overall: `{decision.overall_receipt.sha256}`",
        "",
    ])
    return "\n".join(lines)
