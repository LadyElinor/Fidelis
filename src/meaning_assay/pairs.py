"""Contrasting-pair analysis.

A single case measures the case as much as the framework. The honest unit is the
contrast: run two acts and report how the ranking *moves* between them. The
Kor/Trinity pair is the worked example -- significance holds, warrant inverts --
and that movement, not either ranking alone, is the framework's signal.
"""

from __future__ import annotations

from dataclasses import dataclass

from .engine import Analysis, analyze
from .lenses import LENSBOOK, BY_KEY
from .model import Case, Function, Tradition, Verdict


@dataclass(frozen=True)
class LensDelta:
    key: str
    name: str
    grip_a: int
    grip_b: int
    polarity_a: int
    polarity_b: int
    verdict_a: str
    verdict_b: str

    @property
    def polarity_flipped(self) -> bool:
        return self.polarity_a * self.polarity_b < 0

    @property
    def verdict_flipped(self) -> bool:
        endorse_condemn = {Verdict.ENDORSE.value, Verdict.CONDEMN.value}
        return (
            self.verdict_a in endorse_condemn
            and self.verdict_b in endorse_condemn
            and self.verdict_a != self.verdict_b
        )


@dataclass(frozen=True)
class PairAnalysis:
    a_key: str
    b_key: str
    significance_a: float
    significance_b: float
    warrant_a: float | None
    warrant_b: float | None
    significance_delta: float
    warrant_delta: float | None
    significance_stable: bool
    warrant_inverts: bool
    quadrant_a: str
    quadrant_b: str
    verdict_switchers: tuple[str, ...]   # warrant lenses that flipped endorse<->condemn
    polarity_switchers: tuple[str, ...]  # significance lenses whose polarity flipped
    deltas: tuple[LensDelta, ...]

    @property
    def finding(self) -> str:
        sig = "holds" if self.significance_stable else "moves"
        war = "inverts" if self.warrant_inverts else "holds"
        return f"significance {sig}, warrant {war}"


def compare(case_a: Case, case_b: Case,
            lensbook: tuple[Tradition, ...] = LENSBOOK) -> PairAnalysis:
    a: Analysis = analyze(case_a, lensbook)
    b: Analysis = analyze(case_b, lensbook)

    deltas: list[LensDelta] = []
    verdict_switch: list[str] = []
    polarity_switch: list[str] = []

    for t in lensbook:
        ra = case_a.reading_for(t.key)
        rb = case_b.reading_for(t.key)
        assert ra is not None and rb is not None
        d = LensDelta(
            key=t.key, name=t.name,
            grip_a=int(ra.grip), grip_b=int(rb.grip),
            polarity_a=int(ra.polarity), polarity_b=int(rb.polarity),
            verdict_a=ra.verdict.value, verdict_b=rb.verdict.value,
        )
        deltas.append(d)
        if d.verdict_flipped:
            verdict_switch.append(t.key)
        if t.does(Function.SIGNIFICANCE) and d.polarity_flipped:
            polarity_switch.append(t.key)

    sig_delta = round(b.significance - a.significance, 4)
    war_delta = (
        round(b.warrant - a.warrant, 4)
        if (a.warrant is not None and b.warrant is not None) else None
    )
    significance_stable = abs(sig_delta) <= 0.2 and (a.significance_high == b.significance_high)
    warrant_inverts = (
        {a.warrant_band, b.warrant_band} == {"positive", "negative"}
    )

    return PairAnalysis(
        a_key=case_a.key, b_key=case_b.key,
        significance_a=a.significance, significance_b=b.significance,
        warrant_a=a.warrant, warrant_b=b.warrant,
        significance_delta=sig_delta, warrant_delta=war_delta,
        significance_stable=significance_stable, warrant_inverts=warrant_inverts,
        quadrant_a=a.quadrant, quadrant_b=b.quadrant,
        verdict_switchers=tuple(sorted(verdict_switch)),
        polarity_switchers=tuple(sorted(polarity_switch)),
        deltas=tuple(deltas),
    )
