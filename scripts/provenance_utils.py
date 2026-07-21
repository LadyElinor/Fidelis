from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

MANIFEST_COLUMNS = ("name", "prefix", "branch", "commit", "tree", "url", "imported_at_utc")


def canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_hex_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_hex_text(text: str) -> str:
    return sha256_hex_bytes(text.encode("utf-8"))


def canonicalize_github_url(url: str) -> str:
    normalized = url.strip()
    if normalized.endswith(".git"):
        normalized = normalized[:-4]
    return normalized.rstrip("/")


def manifest_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != MANIFEST_COLUMNS:
            raise ValueError("imported source revision manifest has invalid header")
        return [dict(row) for row in reader]
