"""
sophron_tripwire_bridge.py, map upstream SOPHRON signal validation tiers
onto TrustedRuntime's executable trip-validation contract.

Why this exists
---------------
SOPHRON-CER calibrates its alignment signals (SHIFT / GAME / DECEPT /
CORRIG / HUMAN) and tags each with a validation tier (see SOPHRON-CER
ADR-0001):

    field-validated   calibrated against committed real logs
    validated-sim     calibrated against simulated campaigns only
    unvalidated       no recorded calibration

TrustedRuntime has its own maturity contract (shared/enums.py,
shared/models.py, ADR-0001, ADR-0004):

    TripValidationStatus = UNVALIDATED | CALIBRATING | VALIDATED | RETIRED
    A TripwireRecord may set allowed_for_blocking, but per ADR-0004 only a
    VALIDATED tripwire may act as a blocker; CALIBRATING / UNVALIDATED /
    RETIRED stay advisory and must not silently function as trusted
    blockers.

The seam between the two contracts is exactly where false authority would
leak: a signal that is only sim-calibrated upstream must not arrive in TR
carrying blocking authority. This module is the single sanctioned
translation across that seam.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from trusted_runtime.shared.enums import TripValidationStatus
from trusted_runtime.shared.models import TripwireRecord

DEFAULT_SOURCE_LAYER = "sophron-cer"

FIELD_VALIDATED = "field-validated"
VALIDATED_SIM = "validated-sim"
UNVALIDATED = "unvalidated"
RETIRED = "retired"

_TIER_MAP: dict[str, tuple[TripValidationStatus, bool, bool]] = {
    FIELD_VALIDATED: (TripValidationStatus.VALIDATED, True, True),
    VALIDATED_SIM: (TripValidationStatus.CALIBRATING, False, True),
    UNVALIDATED: (TripValidationStatus.UNVALIDATED, False, True),
    RETIRED: (TripValidationStatus.RETIRED, False, False),
}

_FAIL_SAFE = (TripValidationStatus.UNVALIDATED, False, True)


class BlockingAuthorityLeak(AssertionError):
    """A non-field-validated signal would gain blocking authority."""


@dataclass
class SophronSignalAttestation:
    """One upstream SOPHRON signal's validation claim."""

    signal_id: str
    tier: str
    rationale: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    source_layer: str = DEFAULT_SOURCE_LAYER
    tier_source: str | None = None


def _normalize_tier(tier: str | None) -> str:
    if not tier:
        return ""
    return str(tier).strip().lower().replace("_", "-")


def _assert_record_invariant(record: TripwireRecord) -> None:
    if record.allowed_for_blocking and record.status is not TripValidationStatus.VALIDATED:
        raise BlockingAuthorityLeak(
            f"tripwire {record.tripwire_id!r} is {record.status.value} but marked blocking-eligible"
        )


def map_signal_to_tripwire(
    attestation: SophronSignalAttestation,
    *,
    strict_unvalidated: bool = False,
) -> TripwireRecord:
    tier = _normalize_tier(attestation.tier)
    status, allowed_for_blocking, allowed_for_advisory = _TIER_MAP.get(tier, _FAIL_SAFE)

    notes: list[str] = []
    if tier not in _TIER_MAP:
        notes.append(f"unrecognized upstream tier {attestation.tier!r}; failed safe to UNVALIDATED")
    if attestation.tier_source:
        notes.append(f"tier provenance: {attestation.tier_source}")
    if tier == VALIDATED_SIM:
        notes.append("sim-calibrated upstream; advisory only until field-validated (ADR-0004)")
    if tier == UNVALIDATED and strict_unvalidated:
        allowed_for_advisory = False
        notes.append("strict_unvalidated: refused for advisory use")

    record = TripwireRecord(
        tripwire_id=attestation.signal_id,
        status=status,
        source_layer=attestation.source_layer or DEFAULT_SOURCE_LAYER,
        rationale=attestation.rationale or f"Upstream SOPHRON tier: {attestation.tier}",
        allowed_for_blocking=allowed_for_blocking,
        allowed_for_advisory=allowed_for_advisory,
        evidence_refs=list(attestation.evidence_refs),
        notes=notes,
    )
    _assert_record_invariant(record)
    return record


def assert_no_blocking_authority_leak(records: list[TripwireRecord]) -> None:
    for record in records:
        _assert_record_invariant(record)


def _coerce_attestation(signal_id: str, value: object) -> SophronSignalAttestation:
    if isinstance(value, str):
        return SophronSignalAttestation(signal_id=signal_id, tier=value)
    if isinstance(value, dict):
        return SophronSignalAttestation(
            signal_id=str(value.get("signal_id", signal_id)),
            tier=str(value.get("tier", value.get("validation_tier", "unvalidated"))),
            rationale=str(value.get("rationale", "")),
            evidence_refs=list(value.get("evidence_refs", []) or []),
            source_layer=str(value.get("source_layer", DEFAULT_SOURCE_LAYER)),
            tier_source=(str(value.get("tier_source")) if value.get("tier_source") is not None else None),
        )
    return SophronSignalAttestation(signal_id=signal_id, tier="unvalidated")


def tripwires_from_sophron_validation(
    sophron_validation: dict | None,
    *,
    strict_unvalidated: bool = False,
) -> list[TripwireRecord]:
    if not sophron_validation or not isinstance(sophron_validation, dict):
        return []

    signals = sophron_validation.get("signals")
    if not isinstance(signals, dict):
        meta = {"schema_version", "generated_at", "source_hash", "baseline_id"}
        signals = {k: v for k, v in sophron_validation.items() if k not in meta}

    records = [
        map_signal_to_tripwire(_coerce_attestation(sig_id, val), strict_unvalidated=strict_unvalidated)
        for sig_id, val in signals.items()
    ]
    assert_no_blocking_authority_leak(records)
    return records
