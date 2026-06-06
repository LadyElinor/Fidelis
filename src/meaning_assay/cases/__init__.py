"""Bundled worked cases. Each reproduces an analysis we performed by hand."""

from __future__ import annotations

from ..model import Case
from . import kor, trinity

REGISTRY: dict[str, Case] = {
    kor.CASE.key: kor.CASE,
    trinity.CASE.key: trinity.CASE,
}


def get(key: str) -> Case:
    if key not in REGISTRY:
        raise KeyError(f"unknown case '{key}'; available: {sorted(REGISTRY)}")
    return REGISTRY[key]
