from __future__ import annotations

from typing import Any


def derive_meaning_case_key(description: str, context: dict[str, Any]) -> tuple[str | None, list[str]]:
    notes: list[str] = []
    if "meaning_case_key" in context:
        notes.append("Used explicit meaning_case_key from action context")
        return str(context["meaning_case_key"]), notes

    text = f"{description} {' '.join(f'{k}:{v}' for k, v in sorted(context.items()))}".lower()
    if "safety-critical" in text or "safety_invariant" in text or "invariant" in text:
        notes.append("Mapped safety-critical invariant change to local meaning-assay case 'attest'")
        return "attest", notes
    if "policy weaken" in text or "silent policy" in text:
        notes.append("Mapped silent policy weakening pattern to local case 'silent_policy_weaken'")
        return "silent_policy_weaken", notes

    notes.append("No meaning-assay case mapping found for ProposedAction")
    return None, notes
