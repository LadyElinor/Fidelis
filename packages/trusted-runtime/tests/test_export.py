from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from trusted_runtime.action_identity import canonical_action_digest
from trusted_runtime.exact_approval import ExactApprovalCommitEmissionState
from trusted_runtime.export import compact_verifier_provenance_summary, export_decision_payload, l4_status_interpretation, to_json_safe
from trusted_runtime.integration.engine import assemble_execution_decision
from trusted_runtime.review import load_review_input
from trusted_runtime.shared.models import ExactApprovalTarget, ProposedAction


ALLOWED_L4_STATUSES = {"VALIDATED", "CALIBRATING", "FAILED", "UNAVAILABLE"}
FIXED_TS = datetime(2026, 7, 1, 22, 11, tzinfo=timezone.utc)


def test_to_json_safe_normalizes_path_and_nested_containers():
    payload = {
        "path": Path("example") / "child",
        "values": ({"mode": "x"}, {"other": Path("nested")}),
        "set_values": {"a", "b"},
    }

    result = to_json_safe(payload)

    assert result["path"] == str(Path("example") / "child")
    assert isinstance(result["values"], list)
    assert isinstance(result["set_values"], list)
    assert all(isinstance(item, str) for item in result["set_values"])


def test_export_decision_payload_is_machine_readable_for_live_decision():
    case_path = Path(__file__).resolve().parents[1] / "examples" / "ai_agent_shell_access.json"
    action = load_review_input(case_path).model_copy(update={"exact_approval_identity": "msg-core-001"})
    decision = assemble_execution_decision(action)

    payload = export_decision_payload(decision)

    assert payload["action_id"] == decision.action_id
    assert payload["risk_state"] == decision.risk_state.value
    assert payload["runtime_disposition"] == decision.runtime_disposition.value
    assert isinstance(payload["integration_mode_report"], dict) or payload["integration_mode_report"] is None
    assert isinstance(payload["cer_bundle"], dict)
    assert isinstance(payload["overall_receipt"], dict)
    assert isinstance(payload["compact_verifier_provenance"], dict)
    assert payload["compact_verifier_provenance"]["exact_approval_identity"] == "msg-core-001"
    assert payload["compact_verifier_provenance"]["exact_approval_scope"] == "state_change"
    assert payload["compact_verifier_provenance"]["idempotency_key"] is None
    assert payload["compact_verifier_provenance"]["idempotency_state"] == {
        "present": False,
        "key": None,
        "duplicate_detected": False,
        "enforcement": "none",
    }
    assert payload["compact_verifier_provenance"]["idempotency_posture"] == {
        "scope": "process_local",
        "durability": "ephemeral",
        "proof_note": "prevents duplicate consequential intent reuse only within the current runtime process",
    }
    assert payload["exact_approval_contract"]["scope"] == "state_change"
    assert payload["exact_approval_contract"]["typed_approval_lifted_from_legacy"] is False
    assert "native typed approval fields are preferred" in payload["exact_approval_contract"]["input_preference"]
    assert payload["compact_verifier_provenance"]["exact_approval_binding"]["present"] is True
    assert payload["compact_verifier_provenance"]["exact_approval_source_digest"] is not None
    assert payload["compact_verifier_provenance"]["exact_approval_target"] == {
        "connector": None,
        "destination": None,
        "arguments": None,
    }
    assert payload["compact_verifier_provenance"]["exact_approval_target_requirements"] == {
        "requires_connector": False,
        "requires_destination": False,
        "requires_arguments": False,
    }
    assert payload["exact_approval_contract"]["target_requirements"] == {
        "requires_connector": False,
        "requires_destination": False,
        "requires_arguments": False,
    }
    assert payload["compact_verifier_provenance"]["exact_approval_commit_preview"]["frame"] == "COMMIT"
    assert payload["compact_verifier_provenance"]["exact_approval_commit_preview"]["action_digest"] == canonical_action_digest(action)
    assert payload["compact_verifier_provenance"]["exact_approval_commit_artifact"]["emitted"] is False
    assert payload["compact_verifier_provenance"]["exact_approval_commit_artifact"]["action_digest"] == canonical_action_digest(action)
    assert payload["compact_verifier_provenance"]["exact_approval_commit_governance_state"] in {"eligible_for_emission", "awaiting_human_or_policy_boundary", "not_eligible_for_emission"}
    assert payload["cer_bundle"]["sophron_validation"]["validation_status"] in ALLOWED_L4_STATUSES
    assert payload["l4_interpretation"] == l4_status_interpretation(payload["cer_bundle"]["sophron_validation"]["validation_status"])
    assert payload["cer_bundle"]["sophron_validation"]["interpretation"] == payload["l4_interpretation"]

    rendered = json.dumps(payload, indent=2)
    reparsed = json.loads(rendered)
    assert reparsed["action_id"] == decision.action_id
    assert reparsed["compact_verifier_provenance"]["exact_approval_identity"] == "msg-core-001"


def test_compact_verifier_provenance_summary_surfaces_exact_approval_identity():
    case_path = Path(__file__).resolve().parents[1] / "examples" / "ai_agent_shell_access.json"
    action = load_review_input(case_path).model_copy(update={"exact_approval_identity": "msg-core-xyz"})
    decision = assemble_execution_decision(action)

    summary = compact_verifier_provenance_summary(decision)

    assert summary["exact_approval_identity"] == "msg-core-xyz"
    assert summary["exact_approval_scope"] == "state_change"
    assert summary["exact_approval_binding"]["exact_approval_identity"] == "msg-core-xyz"
    assert summary["exact_approval_source_digest"] is not None
    assert summary["exact_approval_target"] == {
        "connector": None,
        "destination": None,
        "arguments": None,
    }
    assert summary["exact_approval_target_requirements"] == {
        "requires_connector": False,
        "requires_destination": False,
        "requires_arguments": False,
    }
    assert summary["authority_state_digest_short"] is not None
    assert "native typed approval fields are preferred" in summary["exact_approval_input_preference"]
    assert summary["exact_approval_binding"]["action_digest"] == canonical_action_digest(action)
    assert summary["exact_approval_commit_preview"]["deontic"]["binds"]["message"] == "msg-core-xyz"
    assert summary["exact_approval_commit_preview"]["action_digest"] == canonical_action_digest(action)
    assert summary["exact_approval_commit_artifact"]["emission_state"] in {
        ExactApprovalCommitEmissionState.EMITTABLE.value,
        ExactApprovalCommitEmissionState.STAGED.value,
        ExactApprovalCommitEmissionState.SUPPRESSED.value,
    }
    assert summary["exact_approval_commit_governance_state"] in {"eligible_for_emission", "awaiting_human_or_policy_boundary", "not_eligible_for_emission"}


def test_exact_approval_binding_and_preview_change_when_action_changes():
    case_path = Path(__file__).resolve().parents[1] / "examples" / "ai_agent_shell_access.json"
    base_action = load_review_input(case_path).model_copy(update={"exact_approval_identity": "msg-core-xyz"})
    changed_action = base_action.model_copy(
        update={
            "description": "Review a safety-critical invariant change before execution with expanded destination scope.",
        }
    )

    base_decision = assemble_execution_decision(base_action)
    changed_decision = assemble_execution_decision(changed_action)

    base_binding = base_decision.vita_state["attest_bridge"]["exact_approval_binding"]
    changed_binding = changed_decision.vita_state["attest_bridge"]["exact_approval_binding"]
    base_preview = base_decision.vita_state["attest_bridge"]["exact_approval_commit_preview"]
    changed_preview = changed_decision.vita_state["attest_bridge"]["exact_approval_commit_preview"]

    assert base_binding["action_digest"] != changed_binding["action_digest"]
    assert base_binding["receipt_sha256"] != changed_binding["receipt_sha256"]
    assert base_preview["action_digest"] != changed_preview["action_digest"]
    assert base_preview["receipt_sha256"] != changed_preview["receipt_sha256"]


def test_exact_approval_binding_changes_for_destination_connector_and_argument_mutations():
    base_action = load_review_input(Path(__file__).resolve().parents[1] / "examples" / "ai_agent_shell_access.json").model_copy(
        update={
            "description": "Approve a governed outbound notification.",
            "exact_approval_identity": "msg-core-connector-001",
            "context": {
                "action_scope": "network_fetch",
                "connector": "slack",
                "destination": "ops-alerts",
                "arguments": {"text": "deploy approved", "severity": "high"},
            },
        }
    )
    changed_action = base_action.model_copy(
        update={
            "context": {
                "action_scope": "network_fetch",
                "connector": "email",
                "destination": "finance-alerts",
                "arguments": {"text": "deploy approved", "severity": "critical"},
            },
        }
    )

    base_decision = assemble_execution_decision(base_action)
    changed_decision = assemble_execution_decision(changed_action)

    assert base_decision.vita_state["attest_bridge"]["exact_approval_binding"]["action_digest"] != changed_decision.vita_state["attest_bridge"]["exact_approval_binding"]["action_digest"]
    assert base_decision.vita_state["attest_bridge"]["exact_approval_commit_preview"]["receipt_sha256"] != changed_decision.vita_state["attest_bridge"]["exact_approval_commit_preview"]["receipt_sha256"]


def test_exact_approval_binding_changes_when_source_digest_changes():
    base_action = load_review_input(Path(__file__).resolve().parents[1] / "examples" / "ai_agent_shell_access.json").model_copy(
        update={
            "exact_approval_identity": "msg-core-source-001",
            "context": {
                "action_scope": "state_change",
                "source_digest": "sha256:source-a",
                "changed_files": ["src/core/invariants.py"],
            },
        }
    )
    changed_action = base_action.model_copy(
        update={
            "context": {
                **base_action.context,
                "source_digest": "sha256:source-b",
            },
        }
    )

    base_decision = assemble_execution_decision(base_action)
    changed_decision = assemble_execution_decision(changed_action)

    assert base_decision.vita_state["attest_bridge"]["exact_approval_binding"]["source_digest"] == "sha256:source-a"
    assert changed_decision.vita_state["attest_bridge"]["exact_approval_binding"]["source_digest"] == "sha256:source-b"
    assert base_decision.vita_state["attest_bridge"]["exact_approval_commit_preview"]["source_digest"] == "sha256:source-a"
    assert changed_decision.vita_state["attest_bridge"]["exact_approval_commit_preview"]["source_digest"] == "sha256:source-b"
    assert base_decision.vita_state["attest_bridge"]["exact_approval_binding"]["receipt_sha256"] != changed_decision.vita_state["attest_bridge"]["exact_approval_binding"]["receipt_sha256"]
    assert base_decision.vita_state["attest_bridge"]["exact_approval_commit_preview"]["receipt_sha256"] != changed_decision.vita_state["attest_bridge"]["exact_approval_commit_preview"]["receipt_sha256"]


def test_typed_action_scope_and_source_digest_flow_into_binding_and_preview():
    action = ProposedAction(
        id="test-typed-action-001",
        description="Approve a governed outbound notification.",
        timestamp=FIXED_TS,
        exact_approval_identity="msg-core-typed-001",
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
            "arguments": {"text": "deploy approved"},
        },
    )

    decision = assemble_execution_decision(action)

    assert decision.vita_state["attest_bridge"]["exact_approval_scope"] == "network_fetch"
    assert decision.vita_state["attest_bridge"]["exact_approval_binding"]["source_digest"] == "sha256:typed-source"
    assert decision.vita_state["attest_bridge"]["exact_approval_binding"]["connector"] == "teams"
    assert decision.vita_state["attest_bridge"]["exact_approval_binding"]["destination"] == "typed-target-room"
    assert decision.vita_state["attest_bridge"]["exact_approval_binding"]["arguments"] == {"text": "target body"}
    payload = export_decision_payload(decision)
    assert payload["exact_approval_contract"]["scope"] == "network_fetch"
    assert payload["exact_approval_contract"]["target"] == {
        "connector": "teams",
        "destination": "typed-target-room",
        "arguments": {"text": "target body"},
    }
    assert decision.vita_state["attest_bridge"]["exact_approval_commit_preview"]["source_digest"] == "sha256:typed-source"
    assert decision.vita_state["attest_bridge"]["exact_approval_commit_preview"]["connector"] == "teams"
    assert decision.vita_state["attest_bridge"]["exact_approval_commit_preview"]["destination"] == "typed-target-room"
    assert decision.vita_state["attest_bridge"]["exact_approval_commit_preview"]["arguments"] == {"text": "target body"}
    assert canonical_action_digest(action) == decision.vita_state["attest_bridge"]["exact_approval_binding"]["action_digest"]
    assert payload["compact_verifier_provenance"]["exact_approval_target"] == {
        "connector": "teams",
        "destination": "typed-target-room",
        "arguments": {"text": "target body"},
    }


# Preferred-path end-to-end coverage: typed approval fields should work without any legacy target fields.
def test_typed_only_action_flows_end_to_end_without_legacy_target_fields():
    action = ProposedAction(
        id="test-typed-action-002",
        description="Approve a governed outbound notification through the typed-only path.",
        timestamp=FIXED_TS,
        exact_approval_identity="msg-core-typed-002",
        idempotency_key="idem-typed-only-002",
        action_scope="network_fetch",
        source_digest="sha256:typed-only-source",
        exact_approval_target=ExactApprovalTarget(
            connector="discord",
            destination="typed-only-room",
            arguments={"text": "typed only body"},
        ),
        context={},
    )

    decision = assemble_execution_decision(action)
    payload = export_decision_payload(decision)

    assert decision.vita_state["attest_bridge"]["typed_approval_lifted_from_legacy"] is False
    assert decision.vita_state["attest_bridge"]["exact_approval_binding"]["idempotency_key"] == "idem-typed-only-002"
    assert decision.vita_state["attest_bridge"]["exact_approval_binding"]["connector"] == "discord"
    assert decision.vita_state["attest_bridge"]["exact_approval_binding"]["destination"] == "typed-only-room"
    assert decision.vita_state["attest_bridge"]["exact_approval_binding"]["arguments"] == {"text": "typed only body"}
    assert payload["exact_approval_contract"]["typed_approval_lifted_from_legacy"] is False
    assert payload["exact_approval_contract"]["idempotency_key"] == "idem-typed-only-002"
    assert payload["exact_approval_contract"]["idempotency_state"] == {
        "present": True,
        "key": "idem-typed-only-002",
        "duplicate_detected": False,
        "enforcement": "none",
    }
    assert payload["exact_approval_contract"]["idempotency_posture"] == {
        "scope": "process_local",
        "durability": "ephemeral",
        "proof_note": "prevents duplicate consequential intent reuse only within the current runtime process",
    }
    assert payload["exact_approval_contract"]["target"] == {
        "connector": "discord",
        "destination": "typed-only-room",
        "arguments": {"text": "typed only body"},
    }
    assert "native typed approval fields are preferred" in payload["exact_approval_contract"]["input_preference"]


# Preferred-path fixture coverage: the typed example should advertise native typed approval usage.
def test_typed_exact_approval_example_exports_preferred_path_signals():
    case_path = Path(__file__).resolve().parents[1] / "examples" / "typed_exact_approval_review.json"
    action = load_review_input(case_path)
    decision = assemble_execution_decision(action)
    payload = export_decision_payload(decision)

    assert payload["exact_approval_contract"]["scope"] == "network_fetch"
    assert payload["exact_approval_contract"]["typed_approval_lifted_from_legacy"] is False
    assert payload["exact_approval_contract"]["target"] == {
        "connector": "discord",
        "destination": "typed-example-room",
        "arguments": {"text": "typed example body"},
    }
    assert "native typed approval fields are preferred" in payload["exact_approval_contract"]["input_preference"]
