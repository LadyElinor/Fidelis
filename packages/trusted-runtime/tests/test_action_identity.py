from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from trusted_runtime.action_identity import canonical_action_digest, canonical_action_identity_payload, effective_action_scope, effective_arguments, effective_connector, effective_destination, effective_source_digest, legacy_approval_target_shim, normalized_exact_approval_view
from trusted_runtime.shared.models import ExactApprovalTarget, ProposedAction


FIXED_TS = datetime(2026, 7, 1, 22, 11, tzinfo=timezone.utc)


def test_canonical_action_digest_is_stable_across_context_key_order():
    first = ProposedAction(
        id="action-digest-001",
        description="Review a safety-critical invariant change before runtime execution.",
        timestamp=FIXED_TS,
        proposed_by="agent",
        exact_approval_identity="msg-core-001",
        context={"b": 2, "a": 1, "change_type": "safety_invariant"},
    )
    second = ProposedAction(
        id="action-digest-001",
        description="Review a safety-critical invariant change before runtime execution.",
        timestamp=FIXED_TS,
        proposed_by="agent",
        exact_approval_identity="msg-core-001",
        context={"change_type": "safety_invariant", "a": 1, "b": 2},
    )

    assert canonical_action_identity_payload(first) == canonical_action_identity_payload(second)
    assert canonical_action_digest(first) == canonical_action_digest(second)


def test_canonical_action_digest_excludes_retired_authority_injection_keys():
    clean = ProposedAction(
        id="action-digest-002",
        description="Review a safety-critical invariant change before runtime execution.",
        timestamp=FIXED_TS,
        proposed_by="agent",
        exact_approval_identity="msg-core-001",
        context={"change_type": "safety_invariant"},
    )
    injected = ProposedAction(
        id="action-digest-002",
        description="Review a safety-critical invariant change before runtime execution.",
        timestamp=FIXED_TS,
        proposed_by="agent",
        exact_approval_identity="msg-core-001",
        context={
            "change_type": "safety_invariant",
            "authority_ref": "approval:injected",
            "authority_grants": ["grant:bad-1"],
        },
    )

    assert canonical_action_digest(clean) == canonical_action_digest(injected)


def test_canonical_action_digest_changes_when_consequential_fields_change():
    base = ProposedAction(
        id="action-digest-003",
        description="Review a safety-critical invariant change before runtime execution.",
        timestamp=FIXED_TS,
        proposed_by="agent",
        exact_approval_identity="msg-core-001",
        context={"change_type": "safety_invariant", "changed_files": ["src/core/invariants.py"]},
    )
    changed_description = base.model_copy(update={"description": "Review a runtime policy change before runtime execution."})
    changed_scope_context = base.model_copy(update={"context": {"change_type": "training_corpus", "changed_files": ["src/core/invariants.py"]}})
    changed_identity = base.model_copy(update={"exact_approval_identity": "msg-core-002"})

    base_digest = canonical_action_digest(base)
    assert canonical_action_digest(changed_description) != base_digest
    assert canonical_action_digest(changed_scope_context) != base_digest
    assert canonical_action_digest(changed_identity) != base_digest


def test_canonical_action_digest_changes_for_roadmap_style_destination_connector_and_argument_mutations():
    base = ProposedAction(
        id="action-digest-004",
        description="Approve a governed outbound notification.",
        timestamp=FIXED_TS,
        proposed_by="agent",
        exact_approval_identity="msg-core-010",
        context={
            "action_scope": "network_fetch",
            "connector": "slack",
            "destination": "ops-alerts",
            "arguments": {"text": "deploy approved", "severity": "high"},
        },
    )
    changed_destination = base.model_copy(
        update={
            "context": {
                **base.context,
                "destination": "finance-alerts",
            }
        }
    )
    changed_connector = base.model_copy(
        update={
            "context": {
                **base.context,
                "connector": "email",
            }
        }
    )
    changed_arguments = base.model_copy(
        update={
            "context": {
                **base.context,
                "arguments": {"text": "deploy approved", "severity": "critical"},
            }
        }
    )

    base_digest = canonical_action_digest(base)
    assert canonical_action_digest(changed_destination) != base_digest
    assert canonical_action_digest(changed_connector) != base_digest
    assert canonical_action_digest(changed_arguments) != base_digest


def test_canonical_action_digest_changes_when_source_digest_changes():
    base = ProposedAction(
        id="action-digest-005",
        description="Review a governed source-backed action.",
        timestamp=FIXED_TS,
        proposed_by="agent",
        exact_approval_identity="msg-core-020",
        context={
            "action_scope": "state_change",
            "source_digest": "sha256:source-a",
            "changed_files": ["src/core/invariants.py"],
        },
    )
    changed = base.model_copy(
        update={
            "context": {
                **base.context,
                "source_digest": "sha256:source-b",
            }
        }
    )

    assert canonical_action_digest(base) != canonical_action_digest(changed)


def test_typed_action_scope_and_source_digest_override_ad_hoc_context_fields():
    action = ProposedAction(
        id="action-digest-006",
        description="Review a governed source-backed action.",
        timestamp=FIXED_TS,
        proposed_by="agent",
        exact_approval_identity="msg-core-021",
        idempotency_key="idem-typed-001",
        action_scope="network_fetch",
        source_digest="sha256:typed-source",
        exact_approval_target=ExactApprovalTarget(
            connector="teams",
            destination="typed-target-room",
            arguments={"text": "target body"},
        ),
        connector="email",
        destination="finance-alerts",
        arguments={"text": "typed body"},
        context={
            "action_scope": "general",
            "source_digest": "sha256:context-source",
            "connector": "slack",
            "destination": "ops-alerts",
            "arguments": {"text": "context body"},
        },
    )

    assert effective_action_scope(action) == "network_fetch"
    assert effective_source_digest(action) == "sha256:typed-source"
    assert effective_connector(action) == "teams"
    assert effective_destination(action) == "typed-target-room"
    assert effective_arguments(action) == {"text": "target body"}
    payload = canonical_action_identity_payload(action)
    assert payload["action_scope"] == "network_fetch"
    assert payload["idempotency_key"] == "idem-typed-001"
    assert payload["source_digest"] == "sha256:typed-source"
    assert payload["connector"] == "teams"
    assert payload["destination"] == "typed-target-room"
    assert payload["arguments"] == {"text": "target body"}

    legacy_connector, legacy_destination, legacy_arguments = legacy_approval_target_shim(action)
    assert legacy_connector == "email"
    assert legacy_destination == "finance-alerts"
    assert legacy_arguments == {"text": "typed body"}

    normalized = normalized_exact_approval_view(action)
    assert normalized.action_scope == "network_fetch"
    assert normalized.idempotency_key == "idem-typed-001"
    assert normalized.source_digest == "sha256:typed-source"
    assert normalized.connector == "teams"
    assert normalized.destination == "typed-target-room"
    assert normalized.arguments == {"text": "target body"}


def test_typed_action_scope_rejects_unknown_literal():
    with pytest.raises(ValidationError):
        ProposedAction(
            id="action-digest-invalid-scope",
            description="Invalid scope test.",
            timestamp=FIXED_TS,
            action_scope="database_write",
        )


def test_proposed_action_rejects_unknown_top_level_fields():
    with pytest.raises(ValidationError):
        ProposedAction.model_validate(
            {
                "id": "action-unknown-top-level-001",
                "description": "Unknown field test.",
                "timestamp": FIXED_TS,
                "unexpected_field": "should fail",
            }
        )


def test_exact_approval_target_rejects_empty_shape_or_blank_strings():
    with pytest.raises(ValidationError):
        ExactApprovalTarget()
    with pytest.raises(ValidationError):
        ExactApprovalTarget(connector="   ")
    with pytest.raises(ValidationError):
        ExactApprovalTarget(destination="")
    with pytest.raises(ValidationError):
        ExactApprovalTarget(arguments={})


def test_network_fetch_scope_requires_connector_and_destination():
    with pytest.raises(ValidationError):
        ProposedAction(
            id="action-network-invalid-001",
            description="Missing connector.",
            timestamp=FIXED_TS,
            action_scope="network_fetch",
            destination="ops-alerts",
        )
    with pytest.raises(ValidationError):
        ProposedAction(
            id="action-network-invalid-002",
            description="Missing destination.",
            timestamp=FIXED_TS,
            action_scope="network_fetch",
            connector="slack",
        )

    action = ProposedAction(
        id="action-network-valid-001",
        description="Valid typed network target.",
        timestamp=FIXED_TS,
        action_scope="network_fetch",
        exact_approval_target=ExactApprovalTarget(
            connector="teams",
            destination="ops-room",
            arguments={"text": "ok"},
        ),
    )
    assert effective_connector(action) == "teams"
    assert effective_destination(action) == "ops-room"


def test_shell_exec_and_package_install_require_non_empty_arguments():
    with pytest.raises(ValidationError):
        ProposedAction(
            id="action-shell-invalid-001",
            description="Missing shell args.",
            timestamp=FIXED_TS,
            action_scope="shell_exec",
        )
    with pytest.raises(ValidationError):
        ProposedAction(
            id="action-package-invalid-001",
            description="Missing package args.",
            timestamp=FIXED_TS,
            action_scope="package_install",
            arguments={},
        )

    shell_action = ProposedAction(
        id="action-shell-valid-001",
        description="Valid shell exec target.",
        timestamp=FIXED_TS,
        action_scope="shell_exec",
        exact_approval_target=ExactApprovalTarget(arguments={"command": "dir"}),
    )
    package_action = ProposedAction(
        id="action-package-valid-001",
        description="Valid package install target.",
        timestamp=FIXED_TS,
        action_scope="package_install",
        arguments={"package": "ruff", "version": "0.6.9"},
    )

    assert effective_arguments(shell_action) == {"command": "dir"}
    assert effective_arguments(package_action) == {"package": "ruff", "version": "0.6.9"}
