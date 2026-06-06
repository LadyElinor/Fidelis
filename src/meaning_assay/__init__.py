"""meaning-assay: a deterministic, receipts-first engine for reading acts through
twenty-seven traditions of meaning, separating significance from warrant.

The central claim, discovered by running contrasting cases, is that "meaning"
hides two questions:

    significance -- does this act matter, and where does its weight come from?
    warrant      -- is the act good; should it have been done?

Most traditions answer only one. An act can be maximal in significance and void
of warrant (the dangerous quadrant). This package makes that split computable.
"""

from __future__ import annotations

from .engine import Analysis, analyze, rank_by_grip, validate, IntegrityError
from .lenses import LENSBOOK, get as get_tradition
from .model import (
    Case,
    Citation,
    Function,
    Grip,
    Polarity,
    Reading,
    Tradition,
    Verdict,
)
from .pairs import PairAnalysis, compare
from .receipts import receipt, verify, lensbook_digest
from .report import render_case, render_pair_summary

__version__ = "0.1.0"

__all__ = [
    "Analysis", "analyze", "rank_by_grip", "validate", "IntegrityError",
    "LENSBOOK", "get_tradition",
    "Case", "Citation", "Function", "Grip", "Polarity", "Reading", "Tradition", "Verdict",
    "PairAnalysis", "compare",
    "receipt", "verify", "lensbook_digest",
    "render_case", "render_pair_summary",
    "__version__",
]
