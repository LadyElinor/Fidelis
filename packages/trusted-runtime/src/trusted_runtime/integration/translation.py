from __future__ import annotations

import re
from typing import Any


TranslationResult = dict[str, Any]


def _result(
    case_key: str,
    *,
    fit_quality: str,
    fit_reason: str,
    matched_signals: list[str],
    alternative_candidates: list[str] | None = None,
    notes: list[str] | None = None,
) -> TranslationResult:
    return {
        "case_key": case_key,
        "fit_quality": fit_quality,
        "fit_reason": fit_reason,
        "matched_signals": matched_signals,
        "alternative_candidates": alternative_candidates or [],
        "notes": notes or [],
        "fallback_used": fit_quality == "fallback",
    }


def _normalize_text(description: str, context: dict[str, Any]) -> str:
    return f"{description} {' '.join(f'{k}:{v}' for k, v in sorted(context.items()))}".lower()


def _contains_signal(text: str, signal: str) -> bool:
    signal = signal.lower()
    if " " in signal or "-" in signal or "_" in signal:
        pattern = r"(?<![a-z0-9])" + re.escape(signal).replace(r"\ ", r"\s+") + r"(?![a-z0-9])"
        return re.search(pattern, text) is not None
    return re.search(r"(?<![a-z0-9])" + re.escape(signal) + r"(?![a-z0-9])", text) is not None


def _matches_any(text: str, signals: tuple[str, ...]) -> list[str]:
    return [signal for signal in signals if _contains_signal(text, signal)]


def derive_meaning_case(description: str, context: dict[str, Any]) -> TranslationResult:
    notes: list[str] = []
    if "meaning_case_key" in context:
        notes.append("Used explicit meaning_case_key from action context")
        return _result(
            str(context["meaning_case_key"]),
            fit_quality="high",
            fit_reason="explicit action-context override",
            matched_signals=["context.meaning_case_key"],
            notes=notes,
        )

    text = _normalize_text(description, context)

    fairness_signals = ("bias", "biased", "disparate impact", "women's college", "screening model", "hiring model", "fairness")
    if matched := _matches_any(text, fairness_signals):
        notes.append("Mapped fairness or disparate-impact pattern to meaning-assay case family 'fairness_disparate_impact'")
        return _result(
            "fairness_disparate_impact",
            fit_quality="high",
            fit_reason="matched fairness/disparate-impact lexical signals",
            matched_signals=matched,
            notes=notes,
        )

    opacity_signals = ("opaque model", "black box", "unverifiable", "transparency", "sepsis", "model effectiveness", "proprietary model")
    if matched := _matches_any(text, opacity_signals):
        notes.append("Mapped opacity or unverifiable-performance pattern to meaning-assay case family 'opacity_unverifiable_performance'")
        return _result(
            "opacity_unverifiable_performance",
            fit_quality="high",
            fit_reason="matched opacity/unverifiable-performance lexical signals",
            matched_signals=matched,
            notes=notes,
        )

    gaming_signals = ("sales pressure", "cross-selling", "unauthorized accounts", "gaming", "metric corruption", "incentive gaming", "blackouts", "market manipulation")
    if matched := _matches_any(text, gaming_signals):
        notes.append("Mapped incentive-gaming or metric-corruption pattern to meaning-assay case family 'incentive_gaming_metric_corruption'")
        return _result(
            "incentive_gaming_metric_corruption",
            fit_quality="high",
            fit_reason="matched incentive-gaming or metric-corruption lexical signals",
            matched_signals=matched,
            notes=notes,
        )

    whistle_signals = ("whistleblow", "whistleblower", "classified leak", "public interest disclosure", "snowden", "surveillance leak")
    if matched := _matches_any(text, whistle_signals):
        notes.append("Mapped whistleblowing or public-interest disclosure pattern to meaning-assay case family 'public_interest_disclosure_whistleblowing'")
        return _result(
            "public_interest_disclosure_whistleblowing",
            fit_quality="high",
            fit_reason="matched whistleblowing/public-interest disclosure lexical signals",
            matched_signals=matched,
            notes=notes,
        )

    concealment_signals = ("conceal losses", "hidden losses", "barings", "nick leeson", "recovery bet", "unauthorized bets")
    if matched := _matches_any(text, concealment_signals):
        notes.append("Mapped concealment or loss-escalation pattern to meaning-assay case family 'concealment_loss_escalation'")
        return _result(
            "concealment_loss_escalation",
            fit_quality="high",
            fit_reason="matched concealment/loss-escalation lexical signals",
            matched_signals=matched,
            notes=notes,
        )

    adversarial_signals = ("chatbot", "trolls", "manipulated into", "abuse-hardening", "adaptive system", "adversarial public")
    if matched := _matches_any(text, adversarial_signals):
        notes.append("Mapped adversarial-exposure-without-hardening pattern to meaning-assay case family 'adversarial_exposure_without_hardening'")
        return _result(
            "adversarial_exposure_without_hardening",
            fit_quality="high",
            fit_reason="matched adversarial exposure/manipulation lexical signals",
            matched_signals=matched,
            notes=notes,
        )

    retraction_signals = ("retraction", "retract paper", "correction of the record", "replication failure", "defamation suit over retraction")
    if matched := _matches_any(text, retraction_signals):
        notes.append("Mapped record-correction or retraction-under-uncertainty pattern to meaning-assay case family 'record_correction_retraction_under_uncertainty'")
        return _result(
            "record_correction_retraction_under_uncertainty",
            fit_quality="high",
            fit_reason="matched retraction/correction lexical signals",
            matched_signals=matched,
            notes=notes,
        )

    accountability_signals = ("self-driving", "autonomous vehicle fatality", "who's at the wheel", "distributed accountability", "safety driver", "disabled automatic braking")
    if matched := _matches_any(text, accountability_signals):
        notes.append("Mapped distributed-accountability or system-harm pattern to meaning-assay case family 'distributed_accountability_system_harm'")
        return _result(
            "distributed_accountability_system_harm",
            fit_quality="high",
            fit_reason="matched distributed-accountability/system-harm lexical signals",
            matched_signals=matched,
            notes=notes,
        )

    db_wipe_signals = ("wipe", "delete database", "drop table", "destroy evidence", "production database")
    if matched := _matches_any(text, db_wipe_signals):
        notes.append("Mapped destructive irreversible data-loss pattern to meaning-assay case 'db_wipe'")
        return _result(
            "db_wipe",
            fit_quality="high",
            fit_reason="matched destructive data-loss lexical signals",
            matched_signals=matched,
            notes=notes,
        )

    silent_policy_signals = ("policy weaken", "silent policy", "remove safety check", "bypass safety", "disable guardrail", "weaken safety")
    if matched := _matches_any(text, silent_policy_signals):
        notes.append("Mapped silent or convenience-driven safety weakening to meaning-assay case 'silent_policy_weaken'")
        return _result(
            "silent_policy_weaken",
            fit_quality="high",
            fit_reason="matched silent safety-weakening lexical signals",
            matched_signals=matched,
            notes=notes,
        )

    early_release_signals = ("early release", "release early", "incomplete control", "urgent release", "ship despite incomplete")
    if matched := _matches_any(text, early_release_signals):
        notes.append("Mapped urgency-driven release under incomplete control to meaning-assay case 'early_release'")
        return _result(
            "early_release",
            fit_quality="high",
            fit_reason="matched early-release/incomplete-control lexical signals",
            matched_signals=matched,
            notes=notes,
        )

    attest_signals = ("safety-critical", "safety_invariant", "invariant", "attest", "self-certify", "self attestation", "self_attested", "claim honesty", "independent corroboration")
    if matched := _matches_any(text, attest_signals):
        notes.append("Mapped self-attestation or invariant-boundary pattern to meaning-assay case 'attest'")
        return _result(
            "attest",
            fit_quality="medium",
            fit_reason="matched self-attestation/invariant lexical signals",
            matched_signals=matched,
            alternative_candidates=["distributed_accountability_system_harm", "opacity_unverifiable_performance"],
            notes=notes,
        )

    over_refusal_signals = ("refuse", "blocked", "confirm_human", "human review", "maintenance", "internal checklist", "reversible")
    if matched := _matches_any(text, over_refusal_signals):
        notes.append("Mapped low-stakes reversible or review-preserving action to meaning-assay case 'over_refusal'")
        return _result(
            "over_refusal",
            fit_quality="medium",
            fit_reason="matched reversible/review-preserving lexical signals",
            matched_signals=matched,
            alternative_candidates=["record_correction_retraction_under_uncertainty"],
            notes=notes,
        )

    if context.get("review_kind") == "pull_request":
        notes.append("Mapped generic pull-request review action to conservative reversible case 'over_refusal'")
        return _result(
            "over_refusal",
            fit_quality="medium",
            fit_reason="generic pull-request review fallback",
            matched_signals=["context.review_kind=pull_request"],
            alternative_candidates=["attest"],
            notes=notes,
        )

    notes.append("No precise meaning-assay case mapping found; using conservative fallback case 'attest' for general governance review")
    return _result(
        "attest",
        fit_quality="fallback",
        fit_reason="generic conservative fallback for unmatched governance action",
        matched_signals=["fallback"],
        alternative_candidates=[
            "opacity_unverifiable_performance",
            "distributed_accountability_system_harm",
            "public_interest_disclosure_whistleblowing",
        ],
        notes=notes,
    )


def derive_meaning_case_key(description: str, context: dict[str, Any]) -> tuple[str | None, list[str]]:
    result = derive_meaning_case(description, context)
    return result["case_key"], list(result.get("notes", []))
