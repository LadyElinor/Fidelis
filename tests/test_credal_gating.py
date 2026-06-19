"""Tests for the credal interval layer and its integration with the
runtime blocking gate."""
from __future__ import annotations

import pytest

from trusted_runtime.integration.policy import (
    BLOCKING_LOWER_BOUND_THRESHOLD,
    credal_blocking_allowed,
    guard_runtime_disposition,
)
from trusted_runtime.shared.credal import (
    CredalInterval,
    clamp_to_status,
    lower_bound_clears,
    min_width_for,
)
from trusted_runtime.shared.enums import AdapterProvenance, RuntimeDisposition, TripValidationStatus
from trusted_runtime.shared.models import TripwireRecord

REAL = {
    "council": AdapterProvenance.REAL,
    "warrant": AdapterProvenance.REAL,
    "cer_bundle": AdapterProvenance.REAL,
}
S = TripValidationStatus


def _blocking(status, credal):
    return TripwireRecord(
        tripwire_id="t",
        status=status,
        source_layer="test",
        allowed_for_blocking=True,
        credal=credal,
    )


# ---- CredalInterval ----

def test_interval_validates_order_and_range():
    assert CredalInterval(lower=0.2, upper=0.8).width == pytest.approx(0.6)
    with pytest.raises(Exception):
        CredalInterval(lower=0.8, upper=0.2)
    with pytest.raises(Exception):
        CredalInterval(lower=-0.1, upper=0.5)


def test_vacuous():
    v = CredalInterval.vacuous()
    assert (v.lower, v.upper) == (0.0, 1.0)


# ---- floors ----

def test_status_floor():
    assert min_width_for(S.VALIDATED) == 0.0
    assert min_width_for(S.CALIBRATING) == 0.30
    assert min_width_for(S.UNVALIDATED) == 1.0
    assert min_width_for(S.RETIRED) == 1.0


def test_independence_floor_widens_and_takes_the_wider():
    assert min_width_for(S.VALIDATED, "self_attested") == 1.0
    assert min_width_for(S.VALIDATED, "same-operator") == 1.0
    assert min_width_for(S.VALIDATED, "independent-third-party") == 0.0
    assert min_width_for(S.UNVALIDATED, "independent-third-party") == 1.0


# ---- clamp ----

def test_clamp_widens_too_tight_calibrating_band():
    c = clamp_to_status(CredalInterval(lower=0.80, upper=0.90), S.CALIBRATING)
    assert c.width == pytest.approx(0.30, abs=1e-9)
    assert c.upper <= 1.0 and c.lower >= 0.0


def test_clamp_unvalidated_is_vacuous():
    c = clamp_to_status(CredalInterval(lower=0.4, upper=0.5), S.UNVALIDATED)
    assert (c.lower, c.upper) == (0.0, 1.0)


def test_clamp_validated_is_unchanged():
    c = clamp_to_status(CredalInterval(lower=0.7, upper=0.8), S.VALIDATED)
    assert (c.lower, c.upper) == (0.7, 0.8)


def test_clamp_none_is_vacuous():
    assert clamp_to_status(None, S.VALIDATED).width == 1.0


def test_self_attested_validated_forced_vacuous():
    c = clamp_to_status(CredalInterval(lower=0.95, upper=0.97), S.VALIDATED, "self_attested")
    assert (c.lower, c.upper) == (0.0, 1.0)


def test_clamp_near_upper_edge_preserves_width():
    c = clamp_to_status(CredalInterval(lower=0.95, upper=1.0), S.CALIBRATING)
    assert c.width == pytest.approx(0.30, abs=1e-9)
    assert c.upper == pytest.approx(1.0)


# ---- gate ----

def test_validated_confident_band_blocks_eligible():
    recs = [_blocking(S.VALIDATED, CredalInterval(lower=0.7, upper=0.85))]
    assert credal_blocking_allowed(recs, blocking_threshold=0.5) is True
    disp, reason = guard_runtime_disposition(RuntimeDisposition.PROCEED, REAL, tripwire_records=recs)
    assert disp is RuntimeDisposition.PROCEED and reason is None


def test_validated_wide_band_routes_to_human():
    recs = [_blocking(S.VALIDATED, CredalInterval(lower=0.3, upper=0.9))]
    assert credal_blocking_allowed(recs, blocking_threshold=0.5) is False
    disp, reason = guard_runtime_disposition(RuntimeDisposition.PROCEED, REAL, tripwire_records=recs)
    assert disp is RuntimeDisposition.CONFIRM_HUMAN
    assert "credal" in reason.lower()


def test_dilation_to_low_floor_routes_to_human():
    recs = [_blocking(S.VALIDATED, CredalInterval(lower=0.45, upper=0.99))]
    disp, _ = guard_runtime_disposition(RuntimeDisposition.PROCEED, REAL, tripwire_records=recs)
    assert disp is RuntimeDisposition.CONFIRM_HUMAN


def test_absent_credal_falls_back_to_tier_gate_non_breaking():
    recs = [_blocking(S.VALIDATED, None)]
    assert credal_blocking_allowed(recs, blocking_threshold=0.5) is True
    disp, reason = guard_runtime_disposition(RuntimeDisposition.PROCEED, REAL, tripwire_records=recs)
    assert disp is RuntimeDisposition.PROCEED and reason is None


def test_calibrating_blocker_still_caught_by_existing_tier_gate():
    recs = [_blocking(S.CALIBRATING, CredalInterval(lower=0.9, upper=0.95))]
    disp, _ = guard_runtime_disposition(RuntimeDisposition.PROCEED, REAL, tripwire_records=recs)
    assert disp is RuntimeDisposition.CONFIRM_HUMAN


def test_advisory_only_record_does_not_trigger_credal_gate():
    advisory = TripwireRecord(
        tripwire_id="t", status=S.CALIBRATING, source_layer="test",
        allowed_for_blocking=False, credal=CredalInterval(lower=0.1, upper=0.2),
    )
    assert credal_blocking_allowed([advisory], blocking_threshold=0.5) is True


def test_threshold_constant_exists():
    assert 0.0 <= BLOCKING_LOWER_BOUND_THRESHOLD <= 1.0
    assert lower_bound_clears(CredalInterval(lower=0.6, upper=0.7), 0.5) is True
