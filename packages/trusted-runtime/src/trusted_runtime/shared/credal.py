"""
credal.py — imprecise-probability layer for tripwire confidence.

Why this exists
---------------
TripValidationStatus already encodes a coarse, ordinal second-order
uncertainty (how much to trust a signal's own calibration). This makes
that quantitative without forcing false precision: a tripwire may carry a
CredalInterval [lower, upper] instead of a point, and the band's *width*
is the score of combined uncertainty (including uncertainty-about-the-
uncertainty). There is deliberately no single scalar "meta-uncertainty"
number — that would be a precise second-order commitment, i.e. the regress
we are refusing. The honest score is tier + band.

Two floors cap how tight a band may legitimately be:

- by maturity tier: an UNVALIDATED or RETIRED signal is forced vacuous
  ([0, 1]); a CALIBRATING (e.g. sim-backed) one cannot claim a band
  tighter than a floor; a VALIDATED one may be as tight as field
  calibration earned.
- by evidence independence: self-attested or same-operator evidence
  cannot narrow the band at all (forced vacuous) — you cannot shrink
  genuine uncertainty about yourself using evidence you produced
  yourself. This is the independence invariant in quantitative form, and
  it mirrors policy.py's existing rule that self-attested/same-operator
  evidence does not count as corroboration. Only independent corroboration
  narrows the band.

The effective floor is the *wider* of the two, so a VALIDATED signal
backed only by self-attested evidence is still forced vacuous and cannot
block.

Decision use (Γ-maximin): blocking eligibility requires the *lower bound*
to clear a threshold — act on the worst case in the set. A wide or
low-floored band therefore cannot block; in TR that routes to
CONFIRM_HUMAN (see integration/policy.py).
"""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from .enums import TripValidationStatus


class CredalInterval(BaseModel):
    """Lower/upper envelope of a credal set over a tripwire's confidence."""

    lower: float = Field(ge=0.0, le=1.0)
    upper: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _ordered(self) -> "CredalInterval":
        if self.upper < self.lower:
            raise ValueError(f"credal upper ({self.upper}) < lower ({self.lower})")
        return self

    @property
    def width(self) -> float:
        return self.upper - self.lower

    @classmethod
    def vacuous(cls) -> "CredalInterval":
        return cls(lower=0.0, upper=1.0)


STATUS_MIN_WIDTH: dict[TripValidationStatus, float] = {
    TripValidationStatus.VALIDATED: 0.0,
    TripValidationStatus.CALIBRATING: 0.30,
    TripValidationStatus.UNVALIDATED: 1.0,
    TripValidationStatus.RETIRED: 1.0,
}

INDEPENDENCE_MIN_WIDTH: dict[str, float] = {
    "independent-third-party": 0.0,
    "verified-local": 0.0,
    "unknown": 0.30,
    "same-operator": 1.0,
    "self_attested": 1.0,
}


def min_width_for(status: TripValidationStatus, weakest_independence: str | None = None) -> float:
    """Effective floor: the wider of the tier and evidence-independence floors."""
    floor = STATUS_MIN_WIDTH.get(status, 1.0)
    if weakest_independence is not None:
        floor = max(floor, INDEPENDENCE_MIN_WIDTH.get(weakest_independence, 0.30))
    return floor


def _widen_to_min_width(lower: float, upper: float, min_width: float) -> tuple[float, float]:
    lower = min(max(lower, 0.0), 1.0)
    upper = min(max(upper, 0.0), 1.0)
    if upper < lower:
        lower, upper = upper, lower
    deficit = min_width - (upper - lower)
    if deficit <= 0.0:
        return lower, upper
    lower -= deficit / 2.0
    upper += deficit / 2.0
    if lower < 0.0:
        upper = min(1.0, upper - lower)
        lower = 0.0
    if upper > 1.0:
        lower = max(0.0, lower - (upper - 1.0))
        upper = 1.0
    return lower, upper


def clamp_to_status(
    credal: CredalInterval | None,
    status: TripValidationStatus,
    weakest_independence: str | None = None,
) -> CredalInterval:
    """Widen a band so it is no tighter than its tier (and, if given, its
    weakest backing evidence) permits. A missing band is treated as vacuous.

    Note on placement: the runtime gate calls this with `status` only,
    because it does not hold the evidence records. The independence floor is
    meant to be applied upstream at record construction (where the backing
    evidence's independence_class is known) by passing `weakest_independence`.
    """
    if credal is None:
        return CredalInterval.vacuous()
    lower, upper = _widen_to_min_width(
        credal.lower, credal.upper, min_width_for(status, weakest_independence)
    )
    return CredalInterval(lower=lower, upper=upper)


def lower_bound_clears(credal: CredalInterval, threshold: float) -> bool:
    """Γ-maximin admissibility: the worst case in the set clears the bar."""
    return credal.lower >= threshold
