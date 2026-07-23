"""Twin tests: the instrument's own falsifier.

A pair analysis (pairs.py) reports how rankings move between any two acts. A
*twin* test is the special pair that audits the instrument itself:

- a **dark twin** is a structural match of an admired act with the goodness
  stripped out and the vocabulary kept. If the instrument scores the twin's
  warrant as high as the original's, the warrant axis was measuring elegance
  (significance in disguise), and the safeguards are decoration.
- a **bright twin** is a structural match with the goodness exaggerated into
  display. If the instrument scores performed virtue above the sincere
  original, the warrant axis was measuring sentiment -- rewarding the halo.

The two twins bracket the instrument from both sides. A luminous verdict is
only informative if its dark inverse comes back dark and its gilded inverse
fails to outshine it. The findings below are therefore verdicts on the
INSTRUMENT, not on the acts: a twin test that fails has refuted the axis.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .lenses import LENSBOOK
from .model import Case, Tradition
from .pairs import PairAnalysis, compare

# A bright twin must beat the original by more than rounding noise before the
# instrument is convicted of rewarding the halo. Declared data; contest it.
HALO_MARGIN = 0.05


class TwinFinding(str, Enum):
    INSTRUMENT_VALIDATED = "instrument_validated"
    MEASURING_ELEGANCE = "measuring_elegance"    # dark twin's warrant failed to invert
    MEASURING_SENTIMENT = "measuring_sentiment"  # bright twin outscored the original
    NOT_A_STRUCTURAL_MATCH = "not_a_structural_match"  # significance moved: malformed twin


@dataclass(frozen=True)
class TwinTest:
    kind: str  # 'dark' | 'bright'
    original_key: str
    twin_key: str
    finding: TwinFinding
    pair: PairAnalysis
    rationale: str


def dark_twin_test(original: Case, dark_twin: Case,
                   lensbook: tuple[Tradition, ...] = LENSBOOK) -> TwinTest:
    """Original is the admired act; dark_twin is its goodness-stripped match.

    Pass condition: significance holds AND warrant inverts downward. A twin
    whose significance moves is not a twin (the test was malformed, and proves
    nothing either way). A true twin whose warrant fails to invert convicts
    the axis of measuring elegance.
    """
    p = compare(original, dark_twin)
    if not p.significance_stable:
        return TwinTest("dark", original.key, dark_twin.key,
                        TwinFinding.NOT_A_STRUCTURAL_MATCH, p,
                        "significance moved between original and twin; the twin is "
                        "malformed and the test is void, not failed")
    inverted_down = (
        p.warrant_inverts
        and p.warrant_a is not None and p.warrant_b is not None
        and p.warrant_b < p.warrant_a
    )
    if inverted_down:
        return TwinTest("dark", original.key, dark_twin.key,
                        TwinFinding.INSTRUMENT_VALIDATED, p,
                        "warrant inverted while significance held: the axis is "
                        "tracking something the structure alone does not carry")
    return TwinTest("dark", original.key, dark_twin.key,
                    TwinFinding.MEASURING_ELEGANCE, p,
                    "the goodness-stripped twin kept the original's warrant: the "
                    "warrant axis was measuring elegance, not the good")


def bright_twin_test(original: Case, bright_twin: Case,
                     lensbook: tuple[Tradition, ...] = LENSBOOK) -> TwinTest:
    """Original is the sincere act; bright_twin exaggerates its goodness into display.

    Pass condition: significance holds AND the gilded twin does NOT outscore
    the sincere original on warrant. An instrument that rewards the halo is
    measuring sentiment.
    """
    p = compare(original, bright_twin)
    if not p.significance_stable:
        return TwinTest("bright", original.key, bright_twin.key,
                        TwinFinding.NOT_A_STRUCTURAL_MATCH, p,
                        "significance moved between original and twin; the twin is "
                        "malformed and the test is void, not failed")
    outshone = (
        p.warrant_a is not None and p.warrant_b is not None
        and p.warrant_b > p.warrant_a + HALO_MARGIN
    )
    if outshone:
        return TwinTest("bright", original.key, bright_twin.key,
                        TwinFinding.MEASURING_SENTIMENT, p,
                        "performed virtue outscored the sincere original: the warrant "
                        "axis is rewarding the halo, not the good")
    return TwinTest("bright", original.key, bright_twin.key,
                    TwinFinding.INSTRUMENT_VALIDATED, p,
                    "the gilded twin failed to outshine the sincere original: the "
                    "axis is not purchasable with display")
