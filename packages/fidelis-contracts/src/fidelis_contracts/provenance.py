from __future__ import annotations

from dataclasses import asdict, dataclass
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
