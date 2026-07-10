from __future__ import annotations

from runtime.models import CaseInput


def evaluate_authority_provenance(case: CaseInput) -> dict[str, object]:
    authorization_basis = case.authority.authorization_basis.strip().lower()
    requester_role = case.authority.requester_role.strip().lower()

    authority_clear = authorization_basis not in {"", "unclear", "unknown", "missing"}
    trusted_role = requester_role not in {"", "unknown", "missing"}

    if authority_clear and trusted_role:
        provenance_status = "traceable"
        available = True
    elif authorization_basis in {"", "missing"} and requester_role in {"", "missing"}:
        provenance_status = "missing"
        available = False
    else:
        provenance_status = "partial"
        available = True

    notes: list[str] = []
    if authority_clear:
        notes.append("Authorization basis is explicit enough to count as a distinct provenance route.")
    elif provenance_status == "missing":
        notes.append("Authorization basis and requester role are missing, so provenance route is unavailable.")
    else:
        notes.append("Authorization basis is unclear, so provenance route is degraded.")
    if trusted_role:
        notes.append(f"Requester role recorded as {requester_role}.")
    elif provenance_status == "missing":
        notes.append("Requester role is missing.")
    else:
        notes.append("Requester role is not clearly identified.")

    return {
        "route": "authority_or_provenance",
        "authority_clear": authority_clear,
        "trusted_role": trusted_role,
        "provenance_status": provenance_status,
        "available": available,
        "malformed": False,
        "notes": notes,
    }
