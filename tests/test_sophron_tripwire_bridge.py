from __future__ import annotations

from trusted_runtime.integration.policy import (
    guard_runtime_disposition,
    validated_tripwire_blocking_allowed,
)
from trusted_runtime.integration.sophron_tripwire_bridge import (
    BlockingAuthorityLeak,
    SophronSignalAttestation,
    assert_no_blocking_authority_leak,
    map_signal_to_tripwire,
    tripwires_from_sophron_validation,
)
from trusted_runtime.shared.enums import (
    AdapterProvenance,
    RuntimeDisposition,
    TripValidationStatus,
)
from trusted_runtime.shared.models import TripwireRecord

REAL = {
    "council": AdapterProvenance.REAL,
    "warrant": AdapterProvenance.REAL,
    "cer_bundle": AdapterProvenance.REAL,
}


def test_field_validated_maps_to_validated_and_is_blocking_eligible():
    rec = map_signal_to_tripwire(SophronSignalAttestation("sophron.decept", "field-validated"))
    assert rec.status is TripValidationStatus.VALIDATED
    assert rec.allowed_for_blocking is True
    assert rec.allowed_for_advisory is True


def test_validated_sim_maps_to_calibrating_advisory_only():
    rec = map_signal_to_tripwire(SophronSignalAttestation("sophron.shift", "validated-sim"))
    assert rec.status is TripValidationStatus.CALIBRATING
    assert rec.allowed_for_blocking is False
    assert rec.allowed_for_advisory is True


def test_unvalidated_advisory_by_default_refused_in_strict():
    rec = map_signal_to_tripwire(SophronSignalAttestation("sophron.game", "unvalidated"))
    assert rec.status is TripValidationStatus.UNVALIDATED
    assert rec.allowed_for_blocking is False
    assert rec.allowed_for_advisory is True

    strict = map_signal_to_tripwire(
        SophronSignalAttestation("sophron.game", "unvalidated"), strict_unvalidated=True
    )
    assert strict.allowed_for_advisory is False


def test_no_sim_or_unvalidated_tier_is_ever_blocking_eligible():
    for tier in ("validated-sim", "unvalidated", "retired", "garbage-tier", "", None):
        rec = map_signal_to_tripwire(SophronSignalAttestation("sophron.x", tier))
        assert rec.allowed_for_blocking is False


def test_unknown_tier_fails_safe_to_unvalidated():
    rec = map_signal_to_tripwire(SophronSignalAttestation("sophron.x", "totally-unknown"))
    assert rec.status is TripValidationStatus.UNVALIDATED
    assert rec.allowed_for_blocking is False
    assert any("unrecognized" in n for n in rec.notes)


def test_tier_normalization_accepts_underscores_and_case():
    rec = map_signal_to_tripwire(SophronSignalAttestation("sophron.x", "Field_Validated"))
    assert rec.status is TripValidationStatus.VALIDATED
    assert rec.allowed_for_blocking is True


def test_bundle_parsing_flat_and_nested_shapes():
    flat = tripwires_from_sophron_validation(
        {"sophron.shift": "validated-sim", "sophron.decept": "field-validated"}
    )
    by_id = {r.tripwire_id: r for r in flat}
    assert by_id["sophron.shift"].status is TripValidationStatus.CALIBRATING
    assert by_id["sophron.shift"].allowed_for_blocking is False
    assert by_id["sophron.decept"].allowed_for_blocking is True

    nested = tripwires_from_sophron_validation(
        {"signals": {"sophron.game": {"tier": "field-validated", "evidence_refs": ["r1"], "tier_source": "sophron-emitted"}},
         "schema_version": "0.1"}
    )
    assert nested[0].allowed_for_blocking is True
    assert nested[0].evidence_refs == ["r1"]
    assert any("tier provenance: sophron-emitted" in note for note in nested[0].notes)


def test_empty_or_missing_validation_yields_no_records():
    assert tripwires_from_sophron_validation(None) == []
    assert tripwires_from_sophron_validation({}) == []


def test_set_guard_rejects_hand_forged_leak():
    forged = TripwireRecord(
        tripwire_id="x",
        status=TripValidationStatus.CALIBRATING,
        source_layer="sophron-cer",
        allowed_for_blocking=True,
    )
    raised = False
    try:
        assert_no_blocking_authority_leak([forged])
    except BlockingAuthorityLeak:
        raised = True
    assert raised


def test_bridge_records_cooperate_with_live_consumptive_guard():
    records = tripwires_from_sophron_validation(
        {"sophron.shift": "validated-sim", "sophron.decept": "field-validated"}
    )
    assert validated_tripwire_blocking_allowed(records) is True
    disp, reason = guard_runtime_disposition(
        RuntimeDisposition.PROCEED, REAL, tripwire_records=records
    )
    assert disp is RuntimeDisposition.PROCEED
    assert reason is None

    forged = TripwireRecord(
        tripwire_id="sophron.shift",
        status=TripValidationStatus.CALIBRATING,
        source_layer="sophron-cer",
        allowed_for_blocking=True,
    )
    assert validated_tripwire_blocking_allowed([forged]) is False
    disp2, _ = guard_runtime_disposition(
        RuntimeDisposition.PROCEED, REAL, tripwire_records=[forged]
    )
    assert disp2 is RuntimeDisposition.CONFIRM_HUMAN
