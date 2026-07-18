from __future__ import annotations

from trusted_runtime.integration.translation import derive_meaning_case, derive_meaning_case_key


def test_maps_destructive_data_loss_to_db_wipe():
    key, notes = derive_meaning_case_key("wipe the production database to simplify operations", {})
    assert key == "db_wipe"
    assert notes


def test_maps_silent_safety_weakening():
    key, _ = derive_meaning_case_key("remove safety check to speed execution without disclosure", {})
    assert key == "silent_policy_weaken"


def test_maps_urgent_incomplete_release():
    key, _ = derive_meaning_case_key("release early despite incomplete control guarantees", {})
    assert key == "early_release"


def test_maps_pull_request_review_to_non_stub_case():
    key, notes = derive_meaning_case_key("review repo integration governance safety multi-step", {"review_kind": "pull_request"})
    assert key == "over_refusal"
    assert notes


def test_general_fallback_is_non_stub_case():
    key, notes = derive_meaning_case_key("general governance review task", {})
    assert key == "attest"
    assert notes


def test_structured_translation_exposes_fit_quality_fields():
    result = derive_meaning_case("remove safety check to speed execution without disclosure", {})
    assert result["case_key"] == "silent_policy_weaken"
    assert result["fit_quality"] == "high"
    assert result["fit_reason"]
    assert result["matched_signals"]
    assert result["fallback_used"] is False


def test_structured_translation_marks_generic_fallback_explicitly():
    result = derive_meaning_case("general governance review task", {})
    assert result["case_key"] == "attest"
    assert result["fit_quality"] == "fallback"
    assert result["fallback_used"] is True
    assert result["alternative_candidates"]


def test_structured_translation_maps_new_fairness_family_provisionally():
    result = derive_meaning_case("A hiring model created disparate impact against women applicants", {})
    assert result["case_key"] == "fairness_disparate_impact"
    assert result["fit_quality"] == "high"


def test_self_attestation_routes_to_attest_before_reversible_review_case():
    description = (
        "Claims under review rely on self-certify logic and independent corroboration is absent. "
        "The consequence could be irreversible in reputational terms."
    )
    result = derive_meaning_case(description, {"evidence_mode": "self_attested"})
    assert result["case_key"] == "attest"
    assert any(signal in result["matched_signals"] for signal in ("self-certify", "self_attested", "independent corroboration"))



def test_irreversible_does_not_false_match_reversible_signal():
    result = derive_meaning_case("This action is irreversible in reputational terms.", {})
    assert "reversible" not in result["matched_signals"]
