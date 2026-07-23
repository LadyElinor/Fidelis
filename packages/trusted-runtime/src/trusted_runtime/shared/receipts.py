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


def strip_receipt_timestamps(payload: Any) -> Any:
    if isinstance(payload, dict):
        cleaned: dict[str, Any] = {}
        for key, value in payload.items():
            if key in {
                "timestamp",
                "export_timestamp",
                "started_at",
                "created_at",
                "generated_at",
                "receipts_dir",
                "outPath",
                "outputDir",
            }:
                continue
            cleaned[key] = strip_receipt_timestamps(value)
        return cleaned
    if isinstance(payload, list):
        return [strip_receipt_timestamps(item) for item in payload]
    return payload
