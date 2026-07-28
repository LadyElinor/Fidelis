from __future__ import annotations

from enum import StrEnum
from typing import Any

from trusted_runtime.shared.models import ActionScope


class ExactApprovalCommitEmissionState(StrEnum):
    EMITTABLE = "emittable"
    STAGED = "staged"
    SUPPRESSED = "suppressed"
    ABSENT = "absent"


def exact_approval_input_preference_note(typed_approval_lifted_from_legacy: bool) -> str:
    if typed_approval_lifted_from_legacy:
        return "typed approval fields were compatibility-lifted from legacy context; native typed fields are preferred"
    return "native typed approval fields are preferred; legacy context shaping is compatibility-only"


def exact_approval_target_requirements(action_scope: ActionScope | str | None) -> dict[str, Any]:
    scope = str(action_scope or "general")
    if scope == "network_fetch":
        return {"requires_connector": True, "requires_destination": True, "requires_arguments": False}
    if scope in {"shell_exec", "package_install"}:
        return {"requires_connector": False, "requires_destination": False, "requires_arguments": True}
    return {"requires_connector": False, "requires_destination": False, "requires_arguments": False}


def exact_approval_commit_governance_state(
    commit_artifact: dict[str, Any] | None,
) -> str:
    raw_emission_state = (commit_artifact or {}).get("emission_state", ExactApprovalCommitEmissionState.ABSENT)
    try:
        emission_state = ExactApprovalCommitEmissionState(raw_emission_state)
    except ValueError:
        return str(raw_emission_state)
    return {
        ExactApprovalCommitEmissionState.EMITTABLE: "eligible_for_emission",
        ExactApprovalCommitEmissionState.STAGED: "awaiting_human_or_policy_boundary",
        ExactApprovalCommitEmissionState.SUPPRESSED: "not_eligible_for_emission",
        ExactApprovalCommitEmissionState.ABSENT: "no_exact_approval_commit_artifact",
    }.get(emission_state, emission_state.value)
