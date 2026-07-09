from __future__ import annotations

import hashlib
import json


def canonical_json_bytes(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(obj: dict) -> str:
    return f"sha256:{sha256_hex(canonical_json_bytes(obj))}"
