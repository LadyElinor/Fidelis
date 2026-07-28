from trusted_runtime.exact_approval import ExactApprovalCommitEmissionState, exact_approval_commit_governance_state, exact_approval_target_requirements


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
