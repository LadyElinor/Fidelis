from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class AdapterProvenance(StrEnum):
    NATIVE = "native"
    DERIVED_ADVISORY = "derived_advisory"
    STUB = "stub"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class SourceIdentity:
    component: str
    version: str | None = None
    commit: str | None = None
    implementation: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ReceiptRef:
    receipt_id: str
    digest: str
    algorithm: str = "sha256"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RuntimeHealthComponent:
    component: str
    adapter_provenance: AdapterProvenance
    derived_advisory: bool
    component_tree: str | None = None
    source: SourceIdentity | None = None
    evidence_surfaces: tuple[str, ...] = ()
    receipt: ReceiptRef | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RuntimeHealthReceipt:
    profile: str
    generated_at: str
    fidelis_commit: str
    profile_digest: str
    dependency_policy_digest: str
    components: tuple[RuntimeHealthComponent, ...]
    receipt_id: str
    receipt_digest: str
    schema_version: str = field(default="runtime-health-0.1", init=False)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
