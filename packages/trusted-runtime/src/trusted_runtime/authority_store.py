"""Orchestrator-owned authority grant store.

This module is a trust root. It is the ONLY legitimate source of authority
resolution in the runtime. Nothing in this file may ever read proposer-
authored content: grants enter exclusively through the explicit insertion
API below, over a closed channel set, with channel-specific evidence
enforced at insertion time. There is deliberately no `proposer` channel and
no pathway to add one without modifying this file and its tests.

Approved design: docs/AUTHORITY_GRANT_STORE.md (mirrors the reviewed design
document). Do not weaken invariants here for convenience.

Structure:
- GrantRecord: immutable, content-addressed (grant_id = sha256 of canonical
  insertion fields). No update primitive exists; supersession is revoke +
  insert, and revocations persist as tombstones.
- Journal: append-only JSONL, hash-linked (prev_entry_hash). Store state at
  any instant is a pure fold over the journal, which is what makes receipt
  digests externally re-checkable.
- Resolution: evaluation-time aware; resolved / revoked / expired /
  unresolved are materially distinct outcomes.
- state_digest(at): sha256 over sorted active grant_ids; recorded into
  receipts as the authority resolver config hash, and re-checkable via
  replay_verify_digest (the rejecter that makes the digest meaningful).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

InsertionChannel = Literal["operator", "policy_boot", "delegation", "external_attested"]
ResolutionStatus = Literal["resolved", "revoked", "expired", "unresolved"]

# Closed set. `external_attested` is declared-but-disabled: naming it makes
# its absence a stated decision; enabling it requires a concrete external
# attester and verification path (deferred by approval).
ENABLED_CHANNELS: frozenset[str] = frozenset({"operator", "policy_boot", "delegation"})

ADMISSIBLE_AUTHORITY_NAMESPACES: frozenset[str] = frozenset(
    {"approval", "policy", "grant", "capability", "sandbox"}
)

AUTHORITY_TYPES: frozenset[str] = frozenset(
    {"HUMAN_APPROVAL", "POLICY", "CAPABILITY", "DELEGATED", "SANDBOX", "NONE"}
)

# Default authority-strength lattice per Attest spec §8A.2: HUMAN_APPROVAL and
# POLICY are the strongest local roots, CAPABILITY inherits its issuing root
# (approximated as one step below roots for store-held capabilities without a
# chain), DELEGATED inherits the minimum of its chain (computed, not looked
# up), SANDBOX authorizes only within containment, NONE is bottom.
DEFAULT_STRENGTH_LATTICE: dict[str, int] = {
    "HUMAN_APPROVAL": 3,
    "POLICY": 3,
    "CAPABILITY": 2,
    "DELEGATED": 2,
    "SANDBOX": 1,
    "NONE": 0,
}

_SCOPE_TOP = "general"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_instant(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class GrantStoreError(ValueError):
    """Raised when an insertion or revocation violates a store invariant."""


class GrantRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    grant_id: str
    ref: str
    granted_type: str
    scope: str
    strength_ceiling: Optional[int] = None
    expires: Optional[str] = None
    delegates_from: Optional[str] = None
    inserted_at: str
    inserted_by: str
    channel: InsertionChannel
    insertion_evidence: str

    @staticmethod
    def compute_grant_id(fields: dict[str, Any]) -> str:
        return sha256(_canonical(fields).encode("utf-8")).hexdigest()


class Tombstone(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    grant_id: str
    revoked_at: str
    revoked_by: str
    reason: str


class StoreResolution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ref: str
    status: ResolutionStatus
    detail: Optional[str] = None
    grant_id: Optional[str] = None
    granted_type: Optional[str] = None
    granted_scope: Optional[str] = None
    strength: Optional[int] = None
    expires: Optional[str] = None
    delegates_from: list[str] = Field(default_factory=list)


class ReplayVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accept: bool
    computed_digest: str
    expected_digest: str
    evaluated_at: str
    reason: str


class AuthorityGrantStore:
    """Append-only, journal-backed grant store.

    All mutation goes through insert_grant / revoke_grant. State is always
    reconstructible as a fold over the journal; when a journal path is given
    the constructor performs that fold, verifying the hash chain.
    """

    def __init__(self, journal_path: Optional[Path] = None,
                 strength_lattice: Optional[dict[str, int]] = None) -> None:
        self.journal_path = Path(journal_path) if journal_path else None
        self.strength_lattice = dict(strength_lattice or DEFAULT_STRENGTH_LATTICE)
        self._grants: dict[str, GrantRecord] = {}
        self._tombstones: dict[str, Tombstone] = {}
        self._last_entry_hash: str = ""
        if self.journal_path and self.journal_path.exists():
            self._load_journal()

    # -- journal ------------------------------------------------------------

    def _load_journal(self) -> None:
        entries = _read_journal_entries(self.journal_path)
        for entry in entries:
            payload = entry["payload"]
            if entry["entry_type"] == "insert":
                record = GrantRecord.model_validate(payload)
                self._grants[record.grant_id] = record
            elif entry["entry_type"] == "revoke":
                stone = Tombstone.model_validate(payload)
                self._tombstones[stone.grant_id] = stone
            else:  # pragma: no cover - journal is store-written
                raise GrantStoreError(f"unknown journal entry type: {entry['entry_type']}")
            self._last_entry_hash = entry["entry_hash"]

    def _append(self, entry_type: str, payload: dict[str, Any]) -> None:
        entry = {
            "entry_type": entry_type,
            "payload": payload,
            "prev_entry_hash": self._last_entry_hash,
        }
        entry["entry_hash"] = sha256(
            _canonical({k: entry[k] for k in ("entry_type", "payload", "prev_entry_hash")}).encode("utf-8")
        ).hexdigest()
        self._last_entry_hash = entry["entry_hash"]
        if self.journal_path:
            self.journal_path.parent.mkdir(parents=True, exist_ok=True)
            with self.journal_path.open("a", encoding="utf-8") as fh:
                fh.write(_canonical(entry) + "\n")

    # -- insertion ----------------------------------------------------------

    def insert_grant(
        self,
        *,
        ref: str,
        granted_type: str,
        scope: str,
        channel: str,
        inserted_by: str,
        insertion_evidence: str,
        expires: Optional[str] = None,
        strength_ceiling: Optional[int] = None,
        delegates_from: Optional[str] = None,
        at: Optional[datetime] = None,
    ) -> GrantRecord:
        now = at or _utcnow()

        # Channel discipline. There is no proposer channel; do not add one.
        if channel not in ENABLED_CHANNELS:
            if channel == "external_attested":
                raise GrantStoreError(
                    "channel 'external_attested' is declared but disabled: no external "
                    "attester and verification path exists yet"
                )
            raise GrantStoreError(f"unknown insertion channel: {channel!r}")

        # Namespace and type discipline (mirrors Attest §8A.2/§8A.3).
        namespace = ref.split(":", 1)[0] if ":" in ref else ""
        if namespace not in ADMISSIBLE_AUTHORITY_NAMESPACES:
            raise GrantStoreError(
                f"ref {ref!r} is not in an admissible authority namespace "
                f"{sorted(ADMISSIBLE_AUTHORITY_NAMESPACES)}"
            )
        if granted_type not in AUTHORITY_TYPES:
            raise GrantStoreError(f"unknown authority type: {granted_type!r}")
        if granted_type == "NONE":
            raise GrantStoreError("NONE is the bottom element and cannot be granted")

        # Channel-specific evidence, enforced at insertion time.
        if not inserted_by.strip():
            raise GrantStoreError("inserted_by principal is required")
        if not insertion_evidence.strip():
            raise GrantStoreError(f"channel {channel!r} requires non-empty insertion_evidence")

        # delegates_from is required iff this is a delegation.
        is_delegation = channel == "delegation" or granted_type == "DELEGATED"
        if is_delegation and not delegates_from:
            raise GrantStoreError("delegation requires delegates_from (parent grant_id)")
        if not is_delegation and delegates_from:
            raise GrantStoreError("delegates_from is only valid for delegation grants")
        if channel == "delegation" and insertion_evidence != delegates_from:
            raise GrantStoreError("delegation channel evidence must be the parent grant_id")

        # Strength ceiling may only clamp downward from the type's position.
        type_strength = self.strength_lattice[granted_type]
        if strength_ceiling is not None:
            if strength_ceiling > type_strength:
                raise GrantStoreError(
                    f"strength_ceiling {strength_ceiling} exceeds {granted_type}'s "
                    f"lattice position {type_strength}; ceilings clamp, never raise"
                )
            if strength_ceiling < 0:
                raise GrantStoreError("strength_ceiling must be non-negative")

        # Delegation ceilings against the parent, enforced at insertion.
        # Attest independently re-verifies the chain at message time; the two
        # enforcement points are deliberate redundancy, not duplication.
        if is_delegation:
            parent = self._grants.get(delegates_from)
            if parent is None:
                raise GrantStoreError(f"parent grant {delegates_from!r} does not exist")
            parent_res = self._resolution_for(parent, now)
            if parent_res.status != "resolved":
                raise GrantStoreError(
                    f"parent grant {delegates_from!r} is {parent_res.status} and cannot delegate"
                )
            if not self._scope_covers(parent.scope, scope):
                raise GrantStoreError(
                    f"delegated scope {scope!r} exceeds parent scope {parent.scope!r}"
                )
            child_strength = self._effective_strength(granted_type, strength_ceiling)
            if child_strength > (parent_res.strength or 0):
                raise GrantStoreError(
                    f"delegated strength {child_strength} exceeds parent strength {parent_res.strength}"
                )
            if parent.expires is not None:
                if expires is None or _parse_instant(expires) > _parse_instant(parent.expires):
                    raise GrantStoreError(
                        "delegated expiry must be set and must not exceed parent expiry"
                    )
            self._assert_no_delegation_cycle(delegates_from)

        # Determinism rule: at most one active grant per ref at any instant.
        existing = self._active_record_for_ref(ref, now)
        if existing is not None:
            raise GrantStoreError(
                f"ref {ref!r} already has an active grant {existing.grant_id}; "
                "revoke it first (supersession is revoke + insert)"
            )

        fields = {
            "ref": ref,
            "granted_type": granted_type,
            "scope": scope,
            "strength_ceiling": strength_ceiling,
            "expires": expires,
            "delegates_from": delegates_from,
            "inserted_at": now.isoformat(),
            "inserted_by": inserted_by,
            "channel": channel,
            "insertion_evidence": insertion_evidence,
        }
        record = GrantRecord(grant_id=GrantRecord.compute_grant_id(fields), **fields)
        self._grants[record.grant_id] = record
        self._append("insert", record.model_dump(mode="json"))
        return record

    def revoke_grant(self, grant_id: str, *, revoked_by: str, reason: str,
                     at: Optional[datetime] = None) -> Tombstone:
        if grant_id not in self._grants:
            raise GrantStoreError(f"grant {grant_id!r} does not exist")
        if grant_id in self._tombstones:
            raise GrantStoreError(f"grant {grant_id!r} is already revoked")
        if not revoked_by.strip() or not reason.strip():
            raise GrantStoreError("revocation requires revoked_by and reason")
        stone = Tombstone(
            grant_id=grant_id,
            revoked_at=(at or _utcnow()).isoformat(),
            revoked_by=revoked_by,
            reason=reason,
        )
        self._tombstones[grant_id] = stone
        self._append("revoke", stone.model_dump(mode="json"))
        return stone

    # -- resolution ---------------------------------------------------------

    def resolve(self, ref: str, at: Optional[datetime] = None) -> StoreResolution:
        now = at or _utcnow()
        records = sorted(
            (g for g in self._grants.values() if g.ref == ref),
            key=lambda g: g.inserted_at,
        )
        if not records:
            return StoreResolution(ref=ref, status="unresolved", detail="no grant record for ref")
        # One-active-per-ref makes "the latest record" the deciding one at any
        # instant; earlier records are necessarily revoked or expired by now.
        latest = records[-1]
        return self._resolution_for(latest, now)

    def _resolution_for(self, record: GrantRecord, at: datetime) -> StoreResolution:
        stone = self._tombstones.get(record.grant_id)
        if stone is not None and _parse_instant(stone.revoked_at) <= at:
            return StoreResolution(
                ref=record.ref, status="revoked", grant_id=record.grant_id,
                detail=f"revoked at {stone.revoked_at} by {stone.revoked_by}: {stone.reason}",
            )
        if record.expires is not None and _parse_instant(record.expires) <= at:
            return StoreResolution(
                ref=record.ref, status="expired", grant_id=record.grant_id,
                expires=record.expires, detail=f"expired at {record.expires}",
            )
        if _parse_instant(record.inserted_at) > at:
            return StoreResolution(
                ref=record.ref, status="unresolved", grant_id=record.grant_id,
                detail=f"not yet inserted at {at.isoformat()}",
            )
        return StoreResolution(
            ref=record.ref,
            status="resolved",
            grant_id=record.grant_id,
            granted_type=record.granted_type,
            granted_scope=record.scope,
            strength=self._effective_strength(record.granted_type, record.strength_ceiling),
            expires=record.expires,
            delegates_from=[record.delegates_from] if record.delegates_from else [],
        )

    def _active_record_for_ref(self, ref: str, at: datetime) -> Optional[GrantRecord]:
        for record in self._grants.values():
            if record.ref == ref and self._resolution_for(record, at).status == "resolved":
                return record
        return None

    def active_record_for_ref(self, ref: str, at: Optional[datetime] = None) -> Optional[GrantRecord]:
        """Public accessor for the active resolved record for a ref at `at`."""
        return self._active_record_for_ref(ref, at or _utcnow())

    def _effective_strength(self, granted_type: str, ceiling: Optional[int]) -> int:
        base = self.strength_lattice[granted_type]
        return min(base, ceiling) if ceiling is not None else base

    @staticmethod
    def _scope_covers(granted: str, needed: str) -> bool:
        return granted == _SCOPE_TOP or granted == needed

    def _assert_no_delegation_cycle(self, start_grant_id: str) -> None:
        seen: set[str] = set()
        cursor: Optional[str] = start_grant_id
        while cursor:
            if cursor in seen:
                raise GrantStoreError(f"delegation cycle detected at grant {cursor!r}")
            seen.add(cursor)
            record = self._grants.get(cursor)
            cursor = record.delegates_from if record else None

    # -- digest and audit surface --------------------------------------------

    def active_grant_ids(self, at: Optional[datetime] = None) -> list[str]:
        now = at or _utcnow()
        return sorted(
            g.grant_id for g in self._grants.values()
            if self._resolution_for(g, now).status == "resolved"
        )

    def state_digest(self, at: Optional[datetime] = None) -> str:
        return sha256(_canonical(self.active_grant_ids(at)).encode("utf-8")).hexdigest()

    def audit_records(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for record in sorted(self._grants.values(), key=lambda g: g.inserted_at):
            item = record.model_dump(mode="json")
            stone = self._tombstones.get(record.grant_id)
            item["revocation"] = stone.model_dump(mode="json") if stone else None
            out.append(item)
        return out


# -- journal replay: the rejecter ---------------------------------------------

def _read_journal_entries(journal_path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    prev_hash = ""
    for line_no, line in enumerate(journal_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        entry = json.loads(line)
        expected = sha256(
            _canonical({k: entry[k] for k in ("entry_type", "payload", "prev_entry_hash")}).encode("utf-8")
        ).hexdigest()
        if entry.get("entry_hash") != expected:
            raise GrantStoreError(f"journal entry {line_no}: hash mismatch (tampered or corrupt)")
        if entry.get("prev_entry_hash") != prev_hash:
            raise GrantStoreError(f"journal entry {line_no}: broken hash chain")
        prev_hash = entry["entry_hash"]
        entries.append(entry)
    return entries


def replay_verify_digest(journal_path: Path, evaluated_at: str | datetime,
                         expected_digest: str) -> ReplayVerdict:
    """Reconstruct the journal fold at `evaluated_at` and check the digest.

    This is the consumer that makes receipt-bound authority digests
    meaningful: a receipt whose digest cannot be reproduced from the journal
    is REJECTED, not shrugged at.
    """
    at = _parse_instant(evaluated_at)
    try:
        store = AuthorityGrantStore(journal_path=journal_path)
    except (GrantStoreError, json.JSONDecodeError, OSError) as exc:
        return ReplayVerdict(
            accept=False, computed_digest="", expected_digest=expected_digest,
            evaluated_at=at.isoformat(), reason=f"journal fold failed: {exc}",
        )
    computed = store.state_digest(at)
    if computed != expected_digest:
        return ReplayVerdict(
            accept=False, computed_digest=computed, expected_digest=expected_digest,
            evaluated_at=at.isoformat(),
            reason="digest mismatch: receipt does not describe this journal's state at evaluated_at",
        )
    return ReplayVerdict(
        accept=True, computed_digest=computed, expected_digest=expected_digest,
        evaluated_at=at.isoformat(), reason="digest reproduced from journal fold",
    )
