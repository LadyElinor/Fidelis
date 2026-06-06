"""Core data model for meaning-assay.

Everything here is a frozen, hashable value object. The lens definitions and the
per-case readings are *data*, deliberately separated from the engine that scores
them, so that every analytical judgment in the system is inspectable, citable,
and contestable rather than buried in control flow.

Three functions a tradition can perform (a tradition may do several, or none):

- SIGNIFICANCE: it explains where an act gets its weight -- why the act matters,
  who the agent becomes, what is perceived. It locates meaning-as-mattering.
- WARRANT: it carries a standard of the good against which the *act itself* can
  be judged better or worse, right or wrong.
- MECHANISM: it describes a structural, causal, or formal property of
  meaning-making without itself locating significance or supplying a standard
  of the good.

A tradition with an empty function set is a NULL / critical position: it supplies
neither significance nor warrant (this is exactly the role of strict nihilism).

The central thesis of the framework -- discovered by running the Kor and Trinity
cases -- is that the word "meaning" hides two questions, *significance* and
*warrant*, which come apart violently on some acts. The SIGNIFICANCE and WARRANT
functions are the operationalisation of that split.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum


class Function(str, Enum):
    """What a tradition can do for an act."""

    SIGNIFICANCE = "significance"
    WARRANT = "warrant"
    MECHANISM = "mechanism"


class Grip(IntEnum):
    """How firmly a lens engages an act. 'Strain' is honest signal, not failure."""

    STRAINS = 1
    PARTIAL = 2
    FIRM = 3


class Polarity(IntEnum):
    """Does the act exemplify the lens's thesis, contradict it, or neither?"""

    VIOLATES = -1
    NEUTRAL = 0
    AFFIRMS = 1


class Verdict(Enum):
    """A warrant judgment on the act. NA = the lens supplies no standard to judge with."""

    CONDEMN = "condemn"
    MIXED = "mixed"
    ENDORSE = "endorse"
    NA = "na"

    @property
    def value_or_none(self) -> int | None:
        return {"condemn": -1, "mixed": 0, "endorse": 1, "na": None}[self.value]


@dataclass(frozen=True)
class Citation:
    """A pointer to source material. Primary sources are preferred; an outline or
    summary should be marked kind='summary' so downstream readings know to treat
    the reading as provisional."""

    kind: str  # e.g. "primary", "speech", "scholarly", "summary", "scripture"
    label: str
    locator: str | None = None
    url: str | None = None


@dataclass(frozen=True)
class Tradition:
    """One lens. Definitions live in lenses.py and are version-controlled data."""

    numeral: str
    key: str
    name: str
    question: str
    thesis: str
    failure_mode: str
    figures: tuple[str, ...]
    functions: frozenset[Function]
    function_rationale: str

    @property
    def is_null(self) -> bool:
        return len(self.functions) == 0

    def does(self, fn: Function) -> bool:
        return fn in self.functions


@dataclass(frozen=True)
class Reading:
    """An analyst's reading of one act through one lens.

    The reading is the contestable unit. It must carry citations; a reading whose
    only citation is kind='summary' is flagged provisional by the engine.
    """

    tradition_key: str
    grip: Grip
    polarity: Polarity
    failure_tripped: bool
    verdict: Verdict
    note: str
    citations: tuple[Citation, ...] = ()

    @property
    def provisional(self) -> bool:
        if not self.citations:
            return True
        return all(c.kind == "summary" for c in self.citations)


@dataclass(frozen=True)
class Case:
    """An act to be read through every lens."""

    key: str
    title: str
    summary: str
    readings: tuple[Reading, ...]
    sources: tuple[Citation, ...] = ()

    def reading_for(self, tradition_key: str) -> Reading | None:
        for r in self.readings:
            if r.tradition_key == tradition_key:
                return r
        return None
