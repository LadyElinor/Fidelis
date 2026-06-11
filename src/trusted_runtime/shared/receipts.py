from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json_bytes(payload: Any) -> bytes:
    """Canonical JSON for receipt hashing.

    Rules:
    - UTF-8 encoding
    - sorted keys
    - no insignificant whitespace
    - caller is responsible for ensuring wall-clock fields are included intentionally
    """
    return json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_hex(payload: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
