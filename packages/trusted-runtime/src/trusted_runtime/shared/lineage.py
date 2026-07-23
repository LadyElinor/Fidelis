"""
lineage.py — make correlation between assessors visible.

The correlation problem this addresses: several assessors can all report REAL
and agree, yet share an author, a framework, or a source. Then their agreement
is one worldview expressed N times, not N independent confirmations. This module
collapses correlated assessors into independence classes so that same-hand
agreement is never counted as independent corroboration.

LIMIT — read this. The lineage fields below are SELF-REPORTED unless bound to an
externally-rooted identity (a signed manifest, or a reproducible build a third
party can re-derive). This module therefore makes correlation *visible* and
refuses to launder it into independence; it does not by itself prove a claimant
is independent, and it cannot manufacture an independent assessor that does not
exist. Detection and disclosure, not cure. The cure is an external fact.

The same caveat extends to the human escape hatch: CONFIRM_HUMAN is only as
independent as the reviewer it routes to, so `human_reviewer_independence` is
reported as unverified until a reviewer lineage is supplied.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel

_UNKNOWN = "unknown"
_CORRELATION_AXES = ("author_id", "framework_lineage", "source_lineage")


class LineageDescriptor(BaseModel):
    """Provenance-of-the-provenance: who/what produced an assessor."""

    author_id: str = _UNKNOWN
    org_id: str = _UNKNOWN
    framework_lineage: str = _UNKNOWN
    source_lineage: str = _UNKNOWN
    operator_id: str = _UNKNOWN

    def shared_tokens(self) -> set[tuple[str, str]]:
        tokens: set[tuple[str, str]] = set()
        for axis in _CORRELATION_AXES:
            value = getattr(self, axis)
            if value and value != _UNKNOWN:
                tokens.add((axis, value))
        return tokens


def _correlated(a: LineageDescriptor, b: LineageDescriptor) -> bool:
    return bool(a.shared_tokens() & b.shared_tokens())


def independence_classes(descriptors: list[LineageDescriptor]) -> list[list[int]]:
    """Union-find over the correlation relation; returns connected components
    as lists of indices. Each component is one independence class."""
    n = len(descriptors)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(n):
        for j in range(i + 1, n):
            if _correlated(descriptors[i], descriptors[j]):
                parent[find(i)] = find(j)

    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def correlation_report(adapter_lineages: dict[str, LineageDescriptor]) -> dict[str, Any]:
    """Collapse correlated assessors and report whether what looks like
    corroboration is actually independent."""
    names = list(adapter_lineages.keys())
    descriptors = [adapter_lineages[name] for name in names]
    classes = independence_classes(descriptors)
    n_classes = len(classes)
    certification_grade = n_classes >= 2
    named_classes = [sorted(names[i] for i in cls) for cls in classes]

    notes: list[str] = []
    if not certification_grade and len(descriptors) > 1:
        notes.append(
            f"{len(descriptors)} assessors collapse to {n_classes} independence class "
            "(shared author/framework/source); same-hand agreement is not independent "
            "corroboration and must not be treated as certification."
        )

    return {
        "n_assessors": len(descriptors),
        "n_independence_classes": n_classes,
        "certification_grade_corroboration": certification_grade,
        "independence_classes": named_classes,
        "weakest_independence": "independent-third-party" if certification_grade else "same-operator",
        "human_reviewer_independence": "unverified",
        "notes": notes,
    }


def weakest_independence_for_credal(report: dict[str, Any]) -> str:
    return report.get("weakest_independence", "same-operator")
