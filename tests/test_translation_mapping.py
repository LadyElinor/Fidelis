from __future__ import annotations

from trusted_runtime.integration.translation import derive_meaning_case_key


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
