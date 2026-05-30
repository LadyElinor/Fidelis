"""Deterministic hashing utilities for CER envelopes."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

CANONICAL_JSON_VERSION = "canonical-json-v1"


def canonical_json(data: Mapping[str, Any]) -> str:
    """Return stable JSON for hashing.

    The separators and sorted keys are part of the contract. Changing them changes
    hashes, so the canonicalization version is exported separately.
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def deterministic_hash(data: Mapping[str, Any]) -> str:
    """Return SHA-256 hash for canonical JSON payload."""
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()
