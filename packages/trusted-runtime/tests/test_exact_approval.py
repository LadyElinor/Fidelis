from trusted_runtime.exact_approval import ExactApprovalCommitEmissionState, exact_approval_commit_governance_state, exact_approval_target_requirements
from trusted_runtime.integration.engine import ExecutorTransactionIntent, IdempotencyReservationRequest, _attempt_process_local_idempotency_reservation, _should_register_idempotency_key, clear_idempotency_registry, get_runtime_executor, set_runtime_executor
from trusted_runtime.shared.enums import RuntimeDisposition


def test_exact_approval_commit_governance_state_maps_canonical_emission_states():
    assert exact_approval_commit_governance_state(
        {"emission_state": ExactApprovalCommitEmissionState.EMITTABLE.value}
    ) == "eligible_for_emission"
    assert exact_approval_commit_governance_state(
        {"emission_state": ExactApprovalCommitEmissionState.STAGED.value}
    ) == "awaiting_human_or_policy_boundary"
    assert exact_approval_commit_governance_state(
        {"emission_state": ExactApprovalCommitEmissionState.SUPPRESSED.value}
    ) == "not_eligible_for_emission"


def test_exact_approval_commit_governance_state_handles_absent_or_unknown_artifacts():
    assert exact_approval_commit_governance_state(None) == "no_exact_approval_commit_artifact"
    assert exact_approval_commit_governance_state({}) == "no_exact_approval_commit_artifact"
    assert exact_approval_commit_governance_state({"emission_state": "custom-state"}) == "custom-state"


def test_exact_approval_target_requirements_match_current_scope_contract():
    assert exact_approval_target_requirements("network_fetch") == {
        "requires_connector": True,
        "requires_destination": True,
        "requires_arguments": False,
    }
    assert exact_approval_target_requirements("shell_exec") == {
        "requires_connector": False,
        "requires_destination": False,
        "requires_arguments": True,
    }
    assert exact_approval_target_requirements("package_install") == {
        "requires_connector": False,
        "requires_destination": False,
        "requires_arguments": True,
    }
    assert exact_approval_target_requirements("state_change") == {
        "requires_connector": False,
        "requires_destination": False,
        "requires_arguments": False,
    }


def test_idempotency_registration_gate_only_registers_for_proceeding_consequential_paths():
    assert _should_register_idempotency_key(consequential=True, runtime_disposition=RuntimeDisposition.PROCEED) is True
    assert _should_register_idempotency_key(consequential=True, runtime_disposition=RuntimeDisposition.CONFIRM_HUMAN) is False
    assert _should_register_idempotency_key(consequential=True, runtime_disposition=RuntimeDisposition.HALT) is False
    assert _should_register_idempotency_key(consequential=False, runtime_disposition=RuntimeDisposition.PROCEED) is False


def test_process_local_idempotency_reservation_reports_honest_boundary_metadata():
    clear_idempotency_registry()
    deferred = _attempt_process_local_idempotency_reservation(
        IdempotencyReservationRequest(
            key="idem-001",
            exact_approval_scope="state_change",
            runtime_disposition=RuntimeDisposition.CONFIRM_HUMAN,
            transaction_intent=ExecutorTransactionIntent(
                claimed_approval_reference="msg-core-001",
                idempotency_key="idem-001",
                exact_approval_scope="state_change",
                intent_digest="intent-001",
                authorization_binding_digest="binding-001",
                preview_only=True,
            ),
        )
    )
    reserved = _attempt_process_local_idempotency_reservation(
        IdempotencyReservationRequest(
            key="idem-001",
            exact_approval_scope="state_change",
            runtime_disposition=RuntimeDisposition.PROCEED,
            transaction_intent=ExecutorTransactionIntent(
                claimed_approval_reference="msg-core-001",
                idempotency_key="idem-001",
                exact_approval_scope="state_change",
                intent_digest="intent-001",
                authorization_binding_digest="binding-001",
                preview_only=True,
            ),
        )
    )
    duplicate = _attempt_process_local_idempotency_reservation(
        IdempotencyReservationRequest(
            key="idem-001",
            exact_approval_scope="state_change",
            runtime_disposition=RuntimeDisposition.PROCEED,
            transaction_intent=ExecutorTransactionIntent(
                claimed_approval_reference="msg-core-001",
                idempotency_key="idem-001",
                exact_approval_scope="state_change",
                intent_digest="intent-001",
                authorization_binding_digest="binding-001",
                preview_only=True,
            ),
        )
    )

    assert deferred.enforcement == "deferred_until_authorized_execution"
    assert deferred.reservation_attempted is False
    assert deferred.reservation_scope == "process_local"
    assert deferred.reservation_durability == "ephemeral"
    assert deferred.reservation_boundary == "pre_execution_runtime_seam"
    assert deferred.executor_reservation.model_dump(mode="json") == {
        "present": True,
        "key": "idem-001",
        "status": "deferred",
        "executor_interface": "StubRuntimeExecutor.reserve_idempotency",
        "executor_boundary": "not_yet_externalized",
        "durability": "ephemeral",
        "authority_level": "runtime_pre_execution_only",
        "enforcement": "deferred_until_authorized_execution",
        "transaction_intent": {
            "claimed_approval_reference": "msg-core-001",
            "idempotency_key": "idem-001",
            "exact_approval_scope": "state_change",
            "intent_digest": "intent-001",
            "authorization_binding_digest": "binding-001",
            "preview_only": True,
        },
        "receipt": {
            "receipt_kind": "executor_reservation_preview",
            "executor_interface": "StubRuntimeExecutor.reserve_idempotency",
            "reservation_status": "deferred",
            "preview": {
                "execution_branch": "would_execute_on_authorized_path",
                "approval_artifact_verification": "not_verified_in_stub_executor",
                "approval_authority_validation": "not_validated_in_stub_executor",
                "approval_expiry_validation": "not_validated_in_stub_executor",
                "approval_consumption": "would_consume_on_execution",
                "expected_execution_receipt": "would_emit_execution_receipt_on_success",
            },
            "execution_branch_preview_status": "would_execute_on_authorized_path",
            "approval_artifact_verification_status": "not_verified_in_stub_executor",
            "approval_authority_validation_status": "not_validated_in_stub_executor",
            "approval_expiry_validation_status": "not_validated_in_stub_executor",
            "approval_consumption_status": "would_consume_on_execution",
            "expected_execution_receipt_status": "would_emit_execution_receipt_on_success",
            "preview_only": True,
            "durable": False,
            "authority_boundary": "runtime_pre_execution_only",
        },
    }

    assert reserved.enforcement == "registered_pre_execution"
    assert reserved.reservation_attempted is True
    assert reserved.duplicate_detected is False
    assert reserved.executor_reservation.status == "reserved"

    assert duplicate.enforcement == "halt_duplicate_consequential_intent"
    assert duplicate.reservation_attempted is True
    assert duplicate.duplicate_detected is True
    assert duplicate.executor_reservation.status == "duplicate"
    assert duplicate.executor_reservation.receipt.execution_branch_preview_status == "would_not_execute_duplicate"
    assert duplicate.executor_reservation.receipt.approval_consumption_status == "not_consumed_duplicate"
    assert duplicate.executor_reservation.receipt.expected_execution_receipt_status == "would_emit_duplicate_halt_receipt"


def test_runtime_executor_is_replaceable_via_setter():
    original = get_runtime_executor()

    class CustomExecutor:
        def reserve_idempotency(self, request):
            return {
                "present": bool(request.key),
                "key": request.key,
                "duplicate_detected": False,
                "enforcement": "custom",
                "reservation_attempted": True,
                "reservation_scope": "custom",
                "reservation_durability": "custom",
                "reservation_boundary": "custom",
                "executor_reservation": {
                    "present": bool(request.key),
                    "key": request.key,
                    "status": "reserved",
                    "executor_interface": "CustomExecutor.reserve_idempotency",
                    "executor_boundary": "custom",
                    "durability": "custom",
                    "authority_level": "custom",
                    "enforcement": "custom",
                },
            }

    try:
        replaced = set_runtime_executor(CustomExecutor())
        assert replaced.__class__.__name__ == "CustomExecutor"
        assert hasattr(replaced, "reserve_idempotency")
        assert get_runtime_executor().__class__.__name__ == "CustomExecutor"
    finally:
        set_runtime_executor(original)
