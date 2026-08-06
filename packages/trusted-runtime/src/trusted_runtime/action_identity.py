from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from trusted_runtime.shared.models import ProposedAction
from trusted_runtime.shared.receipts import sha256_hex


EXACT_APPROVAL_CONTEXT_EXCLUDE_KEYS = frozenset(
    {
        "authority_ref",
        "authority_refs",
        "authority_grant",
        "authority_grants",
    }
)
_SOURCE_DIGEST_KEYS = ("source_digest", "evidence_digest")


@dataclass(frozen=True)
class NormalizedExactApprovalView:
    action_scope: str | None
    idempotency_key: str | None
    source_digest: str | None
    connector: str | None
    destination: str | None
    arguments: dict[str, Any] | None


def source_digest_from_context(context: dict[str, Any]) -> str | None:
    for key in _SOURCE_DIGEST_KEYS:
        value = context.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    evidence = context.get("evidence")
    if isinstance(evidence, list) and evidence:
        return sha256_hex(evidence)
    return None


def legacy_approval_target_shim(action: ProposedAction) -> tuple[str | None, str | None, dict[str, Any] | None]:
    connector = action.connector.strip() if isinstance(action.connector, str) and action.connector.strip() else None
    if connector is None:
        value = action.context.get("connector")
        connector = value.strip() if isinstance(value, str) and value.strip() else None

    destination = action.destination.strip() if isinstance(action.destination, str) and action.destination.strip() else None
    if destination is None:
        value = action.context.get("destination")
        destination = value.strip() if isinstance(value, str) and value.strip() else None

    if isinstance(action.arguments, dict):
        arguments = action.arguments
    else:
        value = action.context.get("arguments")
        arguments = value if isinstance(value, dict) else None
    return connector, destination, arguments


def normalized_exact_approval_view(action: ProposedAction) -> NormalizedExactApprovalView:
    if isinstance(action.action_scope, str) and action.action_scope.strip():
        action_scope = action.action_scope.strip()
    else:
        value = action.context.get("action_scope")
        action_scope = value.strip() if isinstance(value, str) and value.strip() else None

    if isinstance(action.idempotency_key, str) and action.idempotency_key.strip():
        idempotency_key = action.idempotency_key.strip()
    else:
        value = action.context.get("idempotency_key")
        idempotency_key = value.strip() if isinstance(value, str) and value.strip() else None

    if isinstance(action.source_digest, str) and action.source_digest.strip():
        source_digest = action.source_digest.strip()
    else:
        source_digest = source_digest_from_context(action.context)

    legacy_connector, legacy_destination, legacy_arguments = legacy_approval_target_shim(action)

    if action.exact_approval_target is not None and isinstance(action.exact_approval_target.connector, str) and action.exact_approval_target.connector.strip():
        connector = action.exact_approval_target.connector.strip()
    else:
        connector = legacy_connector

    if action.exact_approval_target is not None and isinstance(action.exact_approval_target.destination, str) and action.exact_approval_target.destination.strip():
        destination = action.exact_approval_target.destination.strip()
    else:
        destination = legacy_destination

    if action.exact_approval_target is not None and isinstance(action.exact_approval_target.arguments, dict):
        arguments = action.exact_approval_target.arguments
    else:
        arguments = legacy_arguments

    return NormalizedExactApprovalView(
        action_scope=action_scope,
        idempotency_key=idempotency_key,
        source_digest=source_digest,
        connector=connector,
        destination=destination,
        arguments=arguments,
    )


def effective_claimed_approval_reference(action: ProposedAction) -> str | None:
    if isinstance(action.claimed_approval_reference, str) and action.claimed_approval_reference.strip():
        return action.claimed_approval_reference.strip()
    if isinstance(action.exact_approval_identity, str) and action.exact_approval_identity.strip():
        return action.exact_approval_identity.strip()
    return None


def effective_action_scope(action: ProposedAction) -> str | None:
    return normalized_exact_approval_view(action).action_scope


def effective_source_digest(action: ProposedAction) -> str | None:
    return normalized_exact_approval_view(action).source_digest


def effective_connector(action: ProposedAction) -> str | None:
    return normalized_exact_approval_view(action).connector


def effective_destination(action: ProposedAction) -> str | None:
    return normalized_exact_approval_view(action).destination


def effective_arguments(action: ProposedAction) -> dict[str, Any] | None:
    return normalized_exact_approval_view(action).arguments


def canonical_intent_identity_payload(action: ProposedAction) -> dict[str, Any]:
    context = {
        key: value
        for key, value in sorted(action.context.items())
        if key not in EXACT_APPROVAL_CONTEXT_EXCLUDE_KEYS
    }
    payload = {
        "id": action.id,
        "description": action.description,
        "context": context,
        "proposed_by": action.proposed_by,
        "idempotency_key": normalized_exact_approval_view(action).idempotency_key,
        "action_scope": effective_action_scope(action),
    }
    source_digest = effective_source_digest(action)
    if source_digest is not None:
        payload["source_digest"] = source_digest
    connector = effective_connector(action)
    if connector is not None:
        payload["connector"] = connector
    destination = effective_destination(action)
    if destination is not None:
        payload["destination"] = destination
    arguments = effective_arguments(action)
    if arguments is not None:
        payload["arguments"] = arguments
    return payload


def canonical_intent_digest(action: ProposedAction) -> str:
    return sha256_hex(canonical_intent_identity_payload(action))


def canonical_action_identity_payload(action: ProposedAction) -> dict[str, Any]:
    payload = canonical_intent_identity_payload(action)
    payload["exact_approval_identity"] = effective_claimed_approval_reference(action)
    payload["claimed_approval_reference"] = effective_claimed_approval_reference(action)
    return payload


def canonical_action_digest(action: ProposedAction) -> str:
    return sha256_hex(canonical_action_identity_payload(action))
