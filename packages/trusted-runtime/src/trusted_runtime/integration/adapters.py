from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from trusted_runtime.shared.models import CERFragmentEnrichment, CERRecordBundle, CouncilAssessment, ProposedAction, WarrantAssay


class HazardAdapter(Protocol):
    def assess(self, action: ProposedAction) -> CouncilAssessment:
        ...


class WarrantAdapter(Protocol):
    def assess(self, action: ProposedAction) -> WarrantAssay:
        ...


class TelemetryAdapter(Protocol):
    def collect(
        self,
        action: ProposedAction,
        runtime_disposition: str,
        cer_enrichment: CERFragmentEnrichment | None = None,
    ) -> CERRecordBundle:
        ...


@dataclass(frozen=True)
class AdapterSet:
    hazard: HazardAdapter
    warrant: WarrantAdapter
    telemetry: TelemetryAdapter
