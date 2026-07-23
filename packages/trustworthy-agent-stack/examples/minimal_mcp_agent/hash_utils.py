"""Deterministic hashing and minimal signing utilities for CER envelopes."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any, Mapping

CANONICAL_JSON_VERSION = "canonical-json-v1"
DEFAULT_SIGNING_KEY_ID = "demo-hmac-key-v1"
DEFAULT_SIGNING_SECRET = "trustworthy-agent-stack-demo-secret"


def canonical_json(data: Mapping[str, Any]) -> str:
    """Return stable JSON for hashing.

    The separators and sorted keys are part of the contract. Changing them changes
    hashes, so the canonicalization version is exported separately.
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def deterministic_hash(data: Mapping[str, Any]) -> str:
    """Return SHA-256 hash for canonical JSON payload."""
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


def sign_payload(data: Mapping[str, Any], *, secret: str = DEFAULT_SIGNING_SECRET) -> str:
    """Return deterministic HMAC-SHA256 signature for canonical JSON payload."""
    return hmac.new(secret.encode("utf-8"), canonical_json(data).encode("utf-8"), hashlib.sha256).hexdigest()


def verify_signature(data: Mapping[str, Any], signature: str, *, secret: str = DEFAULT_SIGNING_SECRET) -> bool:
    """Verify deterministic HMAC-SHA256 signature for canonical JSON payload."""
    expected = sign_payload(data, secret=secret)
    return hmac.compare_digest(expected, signature)
