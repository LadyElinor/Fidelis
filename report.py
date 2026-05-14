from __future__ import annotations

from typing import Dict
import json
from pathlib import Path


def to_markdown(record: Dict) -> str:
    meta = record["meta"]
    synth = record["synthesis"]
    lines = []
    lines.append("# Ethics Council Lite Report")
    lines.append("")
    lines.append(f"**Decision:** {meta['decision']}")
    lines.append(f"**Timestamp:** {meta['timestamp']}")
    lines.append("")
    lines.append("## Stability")
    lines.append("")
    lines.append(f"**Assessment:** {synth['stability_assessment']}")
    lines.append(f"**Suspension triggered:** {'YES' if synth['suspension_protocol_triggered'] else 'No'}")
    if 'minority_report_required' in synth:
        lines.append(f"**Minority report required:** {'YES' if synth['minority_report_required'] else 'No'}")
    if 'detector_overlap_flag' in synth:
        lines.append(f"**Detector overlap flag:** {'YES' if synth['detector_overlap_flag'] else 'No'}")
    if 'representation_limit_assessment' in synth:
        lines.append(f"**Representation limit:** {synth['representation_limit_assessment']}")
    lines.append("")
    lines.append("## Overall recommendation")
    lines.append("")
    lines.append(synth["overall_recommendation"])
    lines.append("")
    if "risk" in record:
        risk = record["risk"]
        lines.append("## Risk instrumentation")
        lines.append("")
        lines.append(f"- Expected harm score: {risk['expected_harm_score']}")
        lines.append(f"- Harm variance: {risk['harm_variance']}")
        lines.append(f"- Tail risk triggered: {'YES' if risk['tail_risk_triggered'] else 'No'}")
        lines.append(f"- Irreversibility risk: {risk['irreversibility_risk']}")
        lines.append(f"- Detector overlap flag: {'YES' if risk['detector_overlap_flag'] else 'No'}")
        if 'alarm_flags' in risk:
            lines.append("- Alarm flags:")
            for key, value in risk['alarm_flags'].items():
                lines.append(f"  - {key}: {'YES' if value else 'No'}")
        lines.append(f"- Materiality flag: {'YES' if risk['materiality_flag'] else 'No'}")
        lines.append(f"- Audit hash: `{risk['audit_hash']}`")
        uncertainty = risk["uncertainty_profile"]
        lines.append("- Uncertainty profile:")
        lines.append(f"  - epistemic: {uncertainty['epistemic']}")
        lines.append(f"  - aleatoric: {uncertainty['aleatoric']}")
        lines.append(f"  - moral: {uncertainty['moral']}")
        lines.append(f"  - composite: {uncertainty['composite']}")
        lines.append("")
    lines.append("## Lens results")
    lines.append("")
    for r in record["round1"]:
        lines.append(f"### {r['agent']}")
        lines.append(f"- Function: {r['function']}")
        lines.append(f"- Verdict: {r['verdict']}")
        lines.append(f"- Confidence: {r['confidence']}")
        if r.get('active') is False:
            note = r['considerations'][0] if r.get('considerations') else 'Not applicable in this case.'
            lines.append(f"- Status: {note}")
        if r['concerns']:
            lines.append("- Concerns:")
            for c in r['concerns']:
                lines.append(f"  - {c}")
        if r['questions']:
            lines.append("- Questions:")
            for q in r['questions']:
                lines.append(f"  - {q}")
        lines.append("")
    if synth['convergence_map']:
        lines.append("## Convergences")
        lines.append("")
        for c in synth['convergence_map']:
            lines.append(f"- {c['point']} ({', '.join(c['agents'])})")
        lines.append("")
    if synth['fault_lines']:
        lines.append("## Fault lines")
        lines.append("")
        for f in synth['fault_lines']:
            lines.append(f"- {f['fault_line']} ({', '.join(f['agents'])})")
        lines.append("")
    if 'synthesis_path' in synth:
        path_info = synth['synthesis_path']
        lines.append("## Synthesis audit")
        lines.append("")
        lines.append(f"- Path taken: {path_info.get('path_taken', 'unknown')}")
        if path_info.get('domains_detected_all'):
            lines.append(f"- Domains detected: {', '.join(path_info['domains_detected_all'])}")
        if path_info.get('domains_detected_skipped'):
            lines.append(f"- Domains skipped: {', '.join(path_info['domains_detected_skipped'])}")
        if path_info.get('suspension_reasons'):
            lines.append("- Suspension reasons:")
            for reason in path_info['suspension_reasons']:
                lines.append(f"  - {reason}")
        if path_info.get('unresolved_tension_reasons'):
            lines.append("- Unresolved tension reasons:")
            for reason in path_info['unresolved_tension_reasons']:
                lines.append(f"  - {reason}")
        if path_info.get('alarm_flags'):
            lines.append("- Synthesis alarm flags:")
            for key, value in path_info['alarm_flags'].items():
                lines.append(f"  - {key}: {'YES' if value else 'No'}")
        for key in ['reactive_attention_distortion_risk', 'self_audit_failure_risk', 'moralized_status_reversal_risk', 'status_admiration_distortion_risk', 'procedure_without_purpose_risk', 'asymmetric_risk_transfer_risk', 'actuarial_fairness_gap_risk', 'methodology_opacity_risk', 'stage_one_thinking_risk']:
            if key in path_info:
                lines.append(f"- {key}: {'YES' if path_info[key] else 'No'}")
        if synth.get('representation_limit_reason'):
            lines.append(f"- Representation note: {synth['representation_limit_reason']}")
        lines.append("")
    if synth['unresolved_questions']:
        lines.append("## Unresolved questions")
        lines.append("")
        for q in synth['unresolved_questions']:
            lines.append(f"- {q}")
        lines.append("")
    return '\n'.join(lines)


def save_outputs(record: Dict, base_path: str) -> None:
    base = Path(base_path)
    base.parent.mkdir(parents=True, exist_ok=True)
    with open(str(base) + '.json', 'w', encoding='utf-8') as f:
        json.dump(record, f, indent=2)
    with open(str(base) + '.md', 'w', encoding='utf-8') as f:
        f.write(to_markdown(record))
