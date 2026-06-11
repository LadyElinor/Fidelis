"""The interpretive ledger: an append-only, hash-chained journal of assays.

From the capstone of the curriculum this engine grew up beside: keep a dated
record of interpretations; when new evidence arrives, append the update rather
than rewriting the past; review the ledger for drift -- readings that hardened
without new grounds, confidence that crept up unearned.

Each entry embeds a full receipt and chains to its predecessor by hash, so the
ledger is tamper-evident in both directions: edit an old entry and its receipt
breaks; remove or reorder entries and the chain breaks. review() then reads the
intact history for three kinds of movement:

- REVISION:      the case's readings changed between entries (expected, healthy --
                 judgments are data and data gets revised; the point is that the
                 revision is on the record, not silently overwritten)
- LENSBOOK_DRIFT: the lensbook changed under the same case
- ENGINE_DRIFT:  same case hash, same lensbook, different outputs -- the one
                 that should never happen in a deterministic engine
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .model import Case
from .receipts import receipt as case_receipt
from .receipts import sha256, verify

GENESIS = "0" * 64


@dataclass(frozen=True)
class DriftFlag:
    kind: str  # 'REVISION' | 'LENSBOOK_DRIFT' | 'ENGINE_DRIFT' | 'BROKEN_RECEIPT' | 'BROKEN_CHAIN'
    case_key: str
    sequence_a: int
    sequence_b: int
    detail: str


def _entry_core(sequence: int, prev_sha: str, rec: dict[str, Any],
                note: str, created_at: str | None) -> dict[str, Any]:
    return {
        "sequence": sequence,
        "prev_entry_sha256": prev_sha,
        "note": note,
        "created_at": created_at,
        "receipt": rec,
    }


def append(path: str | Path, case: Case, note: str = "",
           created_at: str | None = None) -> dict[str, Any]:
    """Append one assay of `case` to the ledger at `path` (JSONL, created if absent)."""
    path = Path(path)
    prior = entries(path) if path.exists() else []
    prev_sha = prior[-1]["entry_sha256"] if prior else GENESIS
    core = _entry_core(len(prior), prev_sha, case_receipt(case), note, created_at)
    entry = {**core, "entry_sha256": sha256(core)}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True, ensure_ascii=False) + "\n")
    return entry


def entries(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def verify_chain(path: str | Path) -> list[DriftFlag]:
    """Check every entry hash, every embedded receipt, and every chain link."""
    flags: list[DriftFlag] = []
    prev_sha = GENESIS
    for e in entries(path):
        key = e["receipt"]["inputs"]["case_key"]
        seq = e["sequence"]
        core = {k: v for k, v in e.items() if k != "entry_sha256"}
        if sha256(core) != e["entry_sha256"]:
            flags.append(DriftFlag("BROKEN_RECEIPT", key, seq, seq,
                                   "entry content does not match its own hash"))
        if e["prev_entry_sha256"] != prev_sha:
            flags.append(DriftFlag("BROKEN_CHAIN", key, seq, seq,
                                   "entry does not chain to its predecessor"))
        if not verify(e["receipt"]):
            flags.append(DriftFlag("BROKEN_RECEIPT", key, seq, seq,
                                   "embedded receipt fails verification"))
        prev_sha = e["entry_sha256"]
    return flags


def review(path: str | Path) -> list[DriftFlag]:
    """Read an intact ledger for drift between successive assays of each case."""
    flags = verify_chain(path)
    by_case: dict[str, list[dict[str, Any]]] = {}
    for e in entries(path):
        by_case.setdefault(e["receipt"]["inputs"]["case_key"], []).append(e)
    for key, seq_entries in by_case.items():
        for a, b in zip(seq_entries, seq_entries[1:]):
            ia, ib = a["receipt"]["inputs"], b["receipt"]["inputs"]
            oa, ob = a["receipt"]["outputs"], b["receipt"]["outputs"]
            if ia["lensbook_sha256"] != ib["lensbook_sha256"]:
                flags.append(DriftFlag("LENSBOOK_DRIFT", key, a["sequence"], b["sequence"],
                                       "the lensbook changed between assays"))
            elif ia["case_sha256"] != ib["case_sha256"]:
                flags.append(DriftFlag("REVISION", key, a["sequence"], b["sequence"],
                                       "readings were revised on the record"))
            elif oa != ob:
                flags.append(DriftFlag("ENGINE_DRIFT", key, a["sequence"], b["sequence"],
                                       "identical inputs produced different outputs; "
                                       "determinism is broken"))
    return flags
