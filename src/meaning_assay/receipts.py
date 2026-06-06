"""Receipts. Every analysis emits a deterministic record: a content hash over the
canonical inputs (the lensbook and the case) and over the computed outputs, so
that the same inputs always produce the same manifest and any drift is visible in
a diff. Timestamps, when added, are kept outside the hashed core.

Determinism rules:
- canonical JSON: sorted keys, no insignificant whitespace, UTF-8 preserved
- no wall-clock time inside the hashed payload
- enums and frozensets reduced to sorted primitive forms
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from typing import Any

from .engine import Analysis, analyze
from .lenses import LENSBOOK
from .model import Case, Tradition

SCHEMA = "meaning-assay/receipt@1"


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256(obj: Any) -> str:
    return hashlib.sha256(_canonical(obj).encode("utf-8")).hexdigest()


def _tradition_fingerprint(t: Tradition) -> dict[str, Any]:
    return {
        "key": t.key,
        "numeral": t.numeral,
        "functions": sorted(f.value for f in t.functions),
        "failure_mode": t.failure_mode,
    }


def lensbook_digest(lensbook: tuple[Tradition, ...] = LENSBOOK) -> str:
    return sha256([_tradition_fingerprint(t) for t in lensbook])


def _case_fingerprint(case: Case) -> dict[str, Any]:
    return {
        "key": case.key,
        "title": case.title,
        "readings": [
            {
                "tradition": r.tradition_key,
                "grip": int(r.grip),
                "polarity": int(r.polarity),
                "failure_tripped": r.failure_tripped,
                "verdict": r.verdict.value,
                "citation_kinds": sorted(c.kind for c in r.citations),
            }
            for r in sorted(case.readings, key=lambda x: x.tradition_key)
        ],
    }


def _analysis_payload(a: Analysis) -> dict[str, Any]:
    d = asdict(a)
    # rows are dataclasses -> asdict already expanded them; keep deterministic order
    d["rows"] = sorted(d["rows"], key=lambda r: r["key"])
    return d


def receipt(case: Case, lensbook: tuple[Tradition, ...] = LENSBOOK) -> dict[str, Any]:
    a = analyze(case, lensbook)
    inputs = {
        "lensbook_sha256": lensbook_digest(lensbook),
        "case_sha256": sha256(_case_fingerprint(case)),
        "case_key": case.key,
    }
    outputs = {
        "significance": a.significance,
        "warrant": a.warrant,
        "quadrant": a.quadrant,
        "warrant_band": a.warrant_band,
        "failure_trip_rate": a.failure_trip_rate,
        "failure_tripped": list(a.failure_tripped_keys),
        "provisional": list(a.provisional_keys),
        "warrant_condemning": list(a.warrant_lenses_condemning),
        "warrant_endorsing": list(a.warrant_lenses_endorsing),
    }
    core = {"schema": SCHEMA, "inputs": inputs, "outputs": outputs}
    return {**core, "receipt_sha256": sha256(core)}


def verify(receipt_obj: dict[str, Any]) -> bool:
    """Recompute the content hash and confirm it matches the stored one."""
    stored = receipt_obj.get("receipt_sha256")
    core = {k: receipt_obj[k] for k in ("schema", "inputs", "outputs")}
    return stored == sha256(core)
