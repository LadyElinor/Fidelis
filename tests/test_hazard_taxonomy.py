import pytest

from trusted_runtime.integration.hazard_taxonomy import (
    HazardFamily,
    MitigationIncreasesRiskError,
    RiskLevel,
    apply_mitigations,
    assert_mitigation_does_not_increase_risk,
    build_hazard_profile,
    classify_hazard,
    level_hazard,
)


def test_known_families_classify():
    assert classify_hazard("formation::scale_without_consent") is HazardFamily.FORMATION
    assert classify_hazard("safety-critical invariant changed") is HazardFamily.SAFETY_INVARIANT
    assert classify_hazard("confidentiality breach") is HazardFamily.SECURITY
    assert classify_hazard("this action is permanent and cannot be undone") is HazardFamily.IRREVERSIBILITY


def test_unknown_hazard_is_unclassified_not_dropped():
    h = level_hazard("kantian duty tension the taxonomy has no family for")
    assert h.family is HazardFamily.UNCLASSIFIED
    assert h.initial_level is RiskLevel.MODERATE


def test_initial_level_comes_from_family_floor():
    assert level_hazard("safety_invariant change").initial_level is RiskLevel.SEVERE
    assert level_hazard("formation::canonization_power").initial_level is RiskLevel.MODERATE


def test_residual_defaults_to_initial_before_mitigation():
    h = level_hazard("security integrity risk")
    assert h.residual_level == h.initial_level
    assert not h.is_mitigated and h.mitigation_delta == 0


def test_mitigation_lowers_residual_and_records_delta():
    h = level_hazard("irreversible deployment")
    m = apply_mitigations(h, RiskLevel.LOW, ("sda:staged-rollback", "sda:canary"))
    assert m.residual_level is RiskLevel.LOW
    assert m.is_mitigated and m.mitigation_delta == 2
    assert m.initial_level is RiskLevel.SERIOUS


def test_mitigation_cannot_increase_risk_via_apply():
    h = level_hazard("formation::no_correction_loop")
    with pytest.raises(MitigationIncreasesRiskError, match="never increase"):
        apply_mitigations(h, RiskLevel.SEVERE, ("sda:bogus",))


def test_no_increase_invariant_standalone():
    assert_mitigation_does_not_increase_risk(RiskLevel.SEVERE, RiskLevel.LOW)
    with pytest.raises(MitigationIncreasesRiskError):
        assert_mitigation_does_not_increase_risk(RiskLevel.LOW, RiskLevel.SEVERE)


def test_equal_residual_is_allowed():
    h = level_hazard("autonomy expansion")
    m = apply_mitigations(h, h.initial_level, ("sda:noop-review",))
    assert m.residual_level == h.initial_level and not m.is_mitigated


def test_profile_reads_max_residual_for_gating():
    profile = build_hazard_profile((
        "safety_invariant change",
        "formation::canonization_power",
        "contested value disagreement",
    ))
    assert profile.max_initial_level is RiskLevel.SEVERE
    assert profile.max_residual_level is RiskLevel.SEVERE
    assert "safety_invariant" in profile.families_present
    assert profile.unclassified_count == 0


def test_profile_counts_unclassified_for_monitoring():
    profile = build_hazard_profile((
        "kantian tension", "trustee obligation", "formation::scale_without_consent",
    ))
    assert profile.unclassified_count == 2
    assert HazardFamily.UNCLASSIFIED.value in profile.families_present
