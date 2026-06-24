from __future__ import annotations

from typing import Any


def derive_meaning_case_key(description: str, context: dict[str, Any]) -> tuple[str | None, list[str]]:
    notes: list[str] = []
    if "meaning_case_key" in context:
        notes.append("Used explicit meaning_case_key from action context")
        return str(context["meaning_case_key"]), notes

    text = f"{description} {' '.join(f'{k}:{v}' for k, v in sorted(context.items()))}".lower()

    if any(token in text for token in ("wipe", "delete database", "drop table", "destroy evidence", "production database")):
        notes.append("Mapped destructive irreversible data-loss pattern to meaning-assay case 'db_wipe'")
        return "db_wipe", notes

    if any(token in text for token in ("policy weaken", "silent policy", "remove safety check", "bypass safety", "disable guardrail", "weaken safety")):
        notes.append("Mapped silent or convenience-driven safety weakening to meaning-assay case 'silent_policy_weaken'")
        return "silent_policy_weaken", notes

    if any(token in text for token in ("early release", "release early", "incomplete control", "urgent release", "ship despite incomplete")):
        notes.append("Mapped urgency-driven release under incomplete control to meaning-assay case 'early_release'")
        return "early_release", notes

    if any(token in text for token in ("refuse", "blocked", "confirm_human", "human review", "maintenance", "internal checklist", "reversible")):
        notes.append("Mapped low-stakes reversible or review-preserving action to meaning-assay case 'over_refusal'")
        return "over_refusal", notes

    if any(token in text for token in ("safety-critical", "safety_invariant", "invariant", "attest", "self-certify", "self attestation", "claim honesty")):
        notes.append("Mapped self-attestation or invariant-boundary pattern to meaning-assay case 'attest'")
        return "attest", notes

    if context.get("review_kind") == "pull_request":
        notes.append("Mapped generic pull-request review action to conservative reversible case 'over_refusal'")
        return "over_refusal", notes

    notes.append("No precise meaning-assay case mapping found; using conservative fallback case 'attest' for general governance review")
    return "attest", notes
