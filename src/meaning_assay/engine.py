"""The engine. It computes only structural products from authored data; it never
invents a judgment. Given a Case and the lensbook it returns an Analysis: the
two axes (significance and warrant), the resulting quadrant, the failure-mode
trip rate, and rankings. It also enforces the integrity rule that makes the
significance/warrant split meaningful -- a lens may only return a moral verdict
if it actually carries warrant.
"""

from __future__ import annotations

from dataclasses import dataclass

from .lenses import LENSBOOK, BY_KEY
from .model import Case, Function, Grip, Polarity, Tradition, Verdict

SIG_HIGH = 0.33
WARRANT_BAND = 0.15  # |W| below this is 'contested'

QUADRANTS = {
    (True, "positive"): "LUMINOUS",     # significant and good (e.g. Kor)
    (True, "contested"): "CHARGED",     # significant, morally unsettled
    (True, "negative"): "DANGEROUS",    # significant but condemned (e.g. Trinity)
    (False, "positive"): "QUIET_GOOD",  # good but light
    (False, "contested"): "INERT",
    (False, "negative"): "CORROSIVE",
}


class IntegrityError(ValueError):
    pass


@dataclass(frozen=True)
class LensRow:
    key: str
    name: str
    functions: tuple[str, ...]
    grip: int
    polarity: int
    failure_tripped: bool
    verdict: str
    provisional: bool
    note: str
    repair: str | None = None
    self_certified: bool = False
    dissents: tuple[tuple[str, str, str], ...] = ()  # (analyst, verdict, rationale)


@dataclass(frozen=True)
class Analysis:
    case_key: str
    significance: float          # [0, 1]: engaged weight across meaning-domains
    warrant: float | None        # [-1, 1], or None if no warrant lens delivered a verdict
    significance_high: bool
    warrant_band: str            # 'positive' | 'contested' | 'negative' | 'undetermined'
    quadrant: str
    failure_trip_rate: float
    failure_tripped_keys: tuple[str, ...]
    provisional_keys: tuple[str, ...]
    rows: tuple[LensRow, ...]

    @property
    def warrant_lenses_condemning(self) -> tuple[str, ...]:
        return tuple(
            r.key for r in self.rows
            if Function.WARRANT.value in r.functions and r.verdict == Verdict.CONDEMN.value
        )

    @property
    def warrant_lenses_endorsing(self) -> tuple[str, ...]:
        return tuple(
            r.key for r in self.rows
            if Function.WARRANT.value in r.functions and r.verdict == Verdict.ENDORSE.value
        )

    @property
    def repairs(self) -> dict[str, str]:
        return {r.key: r.repair for r in self.rows if r.repair}

    @property
    def preserved_dissents(self) -> dict[str, tuple[tuple[str, str, str], ...]]:
        """tradition_key -> preserved minority readings (analyst, verdict, rationale).
        Surfaced, attributed, and never aggregated into either axis."""
        return {r.key: r.dissents for r in self.rows if r.dissents}

    @property
    def self_certified_keys(self) -> tuple[str, ...]:
        return tuple(r.key for r in self.rows if r.self_certified)


def validate(case: Case, lensbook: tuple[Tradition, ...] = LENSBOOK) -> None:
    """Raise IntegrityError unless every lens has exactly one reading and no
    non-warrant lens delivers a moral verdict."""
    keys = {t.key for t in lensbook}
    read_keys = [r.tradition_key for r in case.readings]
    if len(read_keys) != len(set(read_keys)):
        raise IntegrityError(f"{case.key}: duplicate readings")
    missing = keys - set(read_keys)
    if missing:
        raise IntegrityError(f"{case.key}: missing readings for {sorted(missing)}")
    extra = set(read_keys) - keys
    if extra:
        raise IntegrityError(f"{case.key}: readings for unknown lenses {sorted(extra)}")
    for r in case.readings:
        t = BY_KEY[r.tradition_key]
        if r.verdict is not Verdict.NA and not t.does(Function.WARRANT):
            raise IntegrityError(
                f"{case.key}/{t.key}: a {sorted(f.value for f in t.functions) or 'null'} "
                f"lens returned verdict '{r.verdict.value}'; only WARRANT lenses may judge the act."
            )
        for d in r.dissents:
            if d.verdict is not Verdict.NA and not t.does(Function.WARRANT):
                raise IntegrityError(
                    f"{case.key}/{t.key}: a dissent by '{d.analyst}' delivers verdict "
                    f"'{d.verdict.value}' through a non-WARRANT lens; preserved minority "
                    f"opinions obey the same integrity rule as majority readings."
                )
        if r.repair is not None:
            if not t.does(Function.WARRANT):
                raise IntegrityError(
                    f"{case.key}/{t.key}: a non-WARRANT lens carries a repair; a repair "
                    f"is an implicit judgment, so only WARRANT lenses may offer one."
                )
            if r.verdict not in (Verdict.CONDEMN, Verdict.MIXED):
                raise IntegrityError(
                    f"{case.key}/{t.key}: repair on a '{r.verdict.value}' verdict; a repair "
                    f"only makes sense where something needs repairing (condemn/mixed)."
                )


def _band(w: float | None) -> str:
    if w is None:
        return "undetermined"
    if w > WARRANT_BAND:
        return "positive"
    if w < -WARRANT_BAND:
        return "negative"
    return "contested"


def analyze(case: Case, lensbook: tuple[Tradition, ...] = LENSBOOK) -> Analysis:
    validate(case, lensbook)

    sig_num = 0.0
    sig_den = 0.0
    war_num = 0.0
    war_den = 0.0
    tripped: list[str] = []
    provisional: list[str] = []
    rows: list[LensRow] = []

    for t in lensbook:
        r = case.reading_for(t.key)
        assert r is not None  # guaranteed by validate
        if t.does(Function.SIGNIFICANCE):
            # Significance is the WEIGHT an act carries across meaning-domains, not
            # whether it is good. A lens that engages the act (polarity != NEUTRAL)
            # registers it as significant in that domain regardless of valence;
            # only NEUTRAL (the lens finds no purchase) adds nothing. This is why a
            # momentous atrocity scores as highly significant: the moral charge
            # lives entirely on the warrant axis below.
            if r.polarity is not Polarity.NEUTRAL:
                sig_num += int(r.grip)
            sig_den += int(Grip.FIRM)
        if t.does(Function.WARRANT) and r.verdict is not Verdict.NA:
            v = r.verdict.value_or_none
            assert v is not None
            war_num += int(r.grip) * v
            war_den += int(r.grip)
        if r.failure_tripped:
            tripped.append(t.key)
        if r.provisional:
            provisional.append(t.key)
        rows.append(
            LensRow(
                key=t.key,
                name=t.name,
                functions=tuple(sorted(f.value for f in t.functions)),
                grip=int(r.grip),
                polarity=int(r.polarity),
                failure_tripped=r.failure_tripped,
                verdict=r.verdict.value,
                provisional=r.provisional,
                note=r.note,
                repair=r.repair,
                self_certified=r.self_certified,
                dissents=tuple((d.analyst, d.verdict.value, d.rationale) for d in r.dissents),
            )
        )

    significance = round(sig_num / sig_den, 4) if sig_den else 0.0
    warrant = round(war_num / war_den, 4) if war_den else None
    sig_high = significance >= SIG_HIGH
    band = _band(warrant)
    quadrant = QUADRANTS.get((sig_high, band), "UNDETERMINED")

    return Analysis(
        case_key=case.key,
        significance=significance,
        warrant=warrant,
        significance_high=sig_high,
        warrant_band=band,
        quadrant=quadrant,
        failure_trip_rate=round(len(tripped) / len(lensbook), 4),
        failure_tripped_keys=tuple(sorted(tripped)),
        provisional_keys=tuple(sorted(provisional)),
        rows=tuple(rows),
    )


def rank_by_grip(case: Case, lensbook: tuple[Tradition, ...] = LENSBOOK) -> tuple[LensRow, ...]:
    """Lenses ordered by how firmly they engage the act, then by polarity, then key.
    Deterministic for equal grips via the key tiebreak."""
    rows = analyze(case, lensbook).rows
    return tuple(sorted(rows, key=lambda r: (-r.grip, -r.polarity, r.key)))
