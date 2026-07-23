from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Iterable

import yaml


class DetectorStatus(str, Enum):
    INACTIVE = "inactive"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


class ConfidenceClass(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EpistemicVerdict(str, Enum):
    USABLE = "usable"
    REVIEWABLE = "reviewable"
    SUSPEND = "suspend"


@dataclass
class CueMatch:
    triggered: bool
    matched_cues: List[str] = field(default_factory=list)
    families: Set[str] = field(default_factory=set)

    def __bool__(self) -> bool:
        return self.triggered


@dataclass
class LensReceipt:
    lens: str
    status: DetectorStatus
    confidence: ConfidenceClass
    trigger_cues: List[str] = field(default_factory=list)
    trigger_family: str = "unclassified"
    all_families: List[str] = field(default_factory=list)
    claims: List[str] = field(default_factory=list)
    missing_evidence: List[str] = field(default_factory=list)
    minority_report: Optional[str] = None
    verdict: str = "CAUTION"
    considerations: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)
    questions: List[str] = field(default_factory=list)
    active: bool = True

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        d["confidence"] = self.confidence.value
        d["all_families"] = list(self.all_families)
        return d


@dataclass
class EpistemicStatus:
    verdict: EpistemicVerdict
    prompt_thinness: str
    missing_context_burden: str
    detector_confidence: ConfidenceClass
    analysis_constraint: Optional[str] = None
    overlap_warning: bool = False
    overlap_families: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["verdict"] = self.verdict.value
        d["detector_confidence"] = self.detector_confidence.value
        return d


class CueFamilyRegistry:
    def __init__(self, families: Dict[str, dict]):
        self._families = families
        self._cue_to_families: Dict[str, List[str]] = defaultdict(list)
        for family_name, family_data in families.items():
            for cue in family_data.get("cues", []) or []:
                self._cue_to_families[cue.lower()].append(family_name)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "CueFamilyRegistry":
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(data.get("families", {}))

    def family_of(self, cue: str) -> List[str]:
        return list(self._cue_to_families.get(cue.lower(), []))

    def all_families(self) -> List[str]:
        return list(self._families.keys())

    def family_description(self, family: str) -> str:
        return self._families.get(family, {}).get("description", "")


def cue_match(
    text: str,
    cues: Iterable[str],
    registry: Optional[CueFamilyRegistry] = None,
) -> CueMatch:
    t = text.lower()
    matched: List[str] = []
    for cue in cues:
        c = cue.lower()
        if c in t:
            matched.append(cue)

    families: Set[str] = set()
    if registry and matched:
        for cue in matched:
            families.update(registry.family_of(cue))

    return CueMatch(
        triggered=bool(matched),
        matched_cues=matched,
        families=families,
    )


def primary_family(matched_cues: List[str], registry: CueFamilyRegistry) -> str:
    if not matched_cues:
        return "unclassified"

    family_counts: Dict[str, int] = defaultdict(int)
    for cue in matched_cues:
        for fam in registry.family_of(cue):
            family_counts[fam] += 1

    if not family_counts:
        return "unclassified"

    max_count = max(family_counts.values())
    candidates = sorted(f for f, c in family_counts.items() if c == max_count)
    return candidates[0]


def overlap_adjusted_signals(receipts: List[LensReceipt]) -> Dict[str, List[LensReceipt]]:
    by_family: Dict[str, List[LensReceipt]] = defaultdict(list)

    for r in receipts:
        if r.status == DetectorStatus.INACTIVE:
            continue
        if r.trigger_family == "unclassified":
            by_family[f"unclassified::{r.lens}"].append(r)
        else:
            by_family[r.trigger_family].append(r)

    return dict(by_family)


def independent_signal_count(adjusted: Dict[str, List[LensReceipt]]) -> int:
    return len(adjusted)


def correlated_family_warnings(
    adjusted: Dict[str, List[LensReceipt]],
    min_detectors: int = 3,
) -> List[Dict]:
    warnings = []
    for family, items in adjusted.items():
        if family.startswith("unclassified::"):
            continue
        if len(items) >= min_detectors:
            warnings.append({
                "family": family,
                "detector_count": len(items),
                "lenses": sorted(r.lens for r in items),
                "shared_cues": sorted(set(cue for r in items for cue in r.trigger_cues)),
            })
    return warnings


def assess_prompt_thinness(prompt: str) -> str:
    p = prompt.lower()
    word_count = len(prompt.split())

    has_specific_actor = any(w in p for w in [
        "we ", "i ", "our ", "the team", "the company", "management",
        "leadership", "the cfo", "the captain", "the board",
    ])
    has_specific_action = any(w in p for w in [
        "deploy", "launch", "fire", "layoff", "lay off", "approve",
        "reclassify", "pull", "divert", "track", "monitor", "rescue",
        "intervene", "suspend", "proceed",
    ])
    has_domain_anchor = any(w in p for w in [
        "patient", "user", "consumer", "investor", "shareholder",
        "civilization", "employee", "civilian", "worker", "child",
        "officer", "crew", "civil liberties", "data",
    ])

    concrete_signals = sum([has_specific_actor, has_specific_action, has_domain_anchor])

    if concrete_signals >= 3:
        return "concrete"
    if concrete_signals >= 1 or word_count >= 30:
        return "moderate"
    return "thin"


def assess_missing_context_burden(receipts: List[LensReceipt]) -> str:
    total_missing = sum(len(r.missing_evidence) for r in receipts if r.active)
    active_count = sum(1 for r in receipts if r.active) or 1
    per_lens = total_missing / active_count

    if per_lens >= 2.0:
        return "high"
    if per_lens >= 0.75:
        return "medium"
    return "low"


def aggregate_detector_confidence(receipts: List[LensReceipt]) -> ConfidenceClass:
    active = [r for r in receipts if r.active]
    if not active:
        return ConfidenceClass.LOW

    high_count = sum(1 for r in active if r.confidence == ConfidenceClass.HIGH)
    low_count = sum(1 for r in active if r.confidence == ConfidenceClass.LOW)

    if high_count > len(active) / 2:
        return ConfidenceClass.HIGH
    if low_count > len(active) / 2:
        return ConfidenceClass.LOW
    return ConfidenceClass.MEDIUM


def classify_epistemic_status(
    prompt: str,
    receipts: List[LensReceipt],
    suspension_required: bool = False,
    impasse_present: bool = False,
) -> EpistemicStatus:
    thinness = assess_prompt_thinness(prompt)
    missing = assess_missing_context_burden(receipts)
    conf = aggregate_detector_confidence(receipts)

    adjusted = overlap_adjusted_signals(receipts)
    warnings = correlated_family_warnings(adjusted)
    overlap_warning = bool(warnings)
    overlap_families = [w["family"] for w in warnings]

    if suspension_required:
        verdict = EpistemicVerdict.SUSPEND
        constraint = "Suspension required by synthesis; do not act on this output without human review."
    elif thinness == "thin" and missing == "high":
        verdict = EpistemicVerdict.SUSPEND
        constraint = "Prompt is too thin and missing-context burden is too high; analysis is not fit for action."
    elif impasse_present:
        verdict = EpistemicVerdict.REVIEWABLE
        constraint = "Canonical impasse surfaced; output is meaningful but cannot be treated as a verdict."
    elif thinness == "thin":
        verdict = EpistemicVerdict.REVIEWABLE
        constraint = "Prompt is thin; output should be inspected before any use."
    elif missing == "high":
        verdict = EpistemicVerdict.REVIEWABLE
        constraint = "Many lenses report missing evidence; output should be inspected before any use."
    elif conf == ConfidenceClass.LOW:
        verdict = EpistemicVerdict.REVIEWABLE
        constraint = "Detector confidence is low; treat output as a hazard map, not a verdict."
    else:
        verdict = EpistemicVerdict.USABLE
        constraint = None

    return EpistemicStatus(
        verdict=verdict,
        prompt_thinness=thinness,
        missing_context_burden=missing,
        detector_confidence=conf,
        analysis_constraint=constraint,
        overlap_warning=overlap_warning,
        overlap_families=overlap_families,
    )


def assemble_hazards(receipts: List[LensReceipt]) -> List[Dict]:
    adjusted = overlap_adjusted_signals(receipts)
    hazards = []

    for family, items in adjusted.items():
        all_cues = sorted(set(cue for r in items for cue in r.trigger_cues))
        all_claims = []
        for r in items:
            all_claims.extend(r.claims)

        status_order = {
            DetectorStatus.WEAK: 1,
            DetectorStatus.MODERATE: 2,
            DetectorStatus.STRONG: 3,
        }
        peak_status = max(items, key=lambda r: status_order.get(r.status, 0)).status

        hazards.append({
            "trigger_family": family,
            "detector_status": peak_status.value,
            "supporting_lenses": sorted(r.lens for r in items),
            "trigger_cues": all_cues,
            "claims": all_claims,
            "missing_evidence": sorted(set(ev for r in items for ev in r.missing_evidence)),
        })

    sort_order = {"strong": 0, "moderate": 1, "weak": 2}
    hazards.sort(key=lambda h: sort_order.get(h["detector_status"], 99))
    return hazards


def receipt_from_legacy_result(
    legacy_result,
    matched_cues: List[str],
    registry: CueFamilyRegistry,
    missing_evidence: Optional[List[str]] = None,
    minority_report: Optional[str] = None,
) -> LensReceipt:
    if not getattr(legacy_result, "active", True):
        status = DetectorStatus.INACTIVE
    elif legacy_result.confidence < 0.5:
        status = DetectorStatus.INACTIVE
    elif legacy_result.confidence < 0.7:
        status = DetectorStatus.WEAK
    elif legacy_result.confidence < 0.85:
        status = DetectorStatus.MODERATE
    else:
        status = DetectorStatus.STRONG

    if legacy_result.confidence < 0.65:
        conf = ConfidenceClass.LOW
    elif legacy_result.confidence < 0.85:
        conf = ConfidenceClass.MEDIUM
    else:
        conf = ConfidenceClass.HIGH

    primary = primary_family(matched_cues, registry)
    all_fams = sorted(set(f for cue in matched_cues for f in registry.family_of(cue)))

    return LensReceipt(
        lens=legacy_result.agent,
        status=status,
        confidence=conf,
        trigger_cues=matched_cues,
        trigger_family=primary,
        all_families=all_fams,
        claims=list(legacy_result.concerns),
        missing_evidence=missing_evidence or [],
        minority_report=minority_report,
        verdict=legacy_result.verdict,
        considerations=list(legacy_result.considerations),
        concerns=list(legacy_result.concerns),
        questions=list(legacy_result.questions),
        active=legacy_result.active,
    )


def instrument_synthesis(
    prompt: str,
    receipts: List[LensReceipt],
    suspension_required: bool = False,
    impasse_present: bool = False,
) -> Dict:
    status = classify_epistemic_status(
        prompt, receipts, suspension_required, impasse_present
    )
    adjusted = overlap_adjusted_signals(receipts)
    warnings = correlated_family_warnings(adjusted)
    hazards = assemble_hazards(receipts)

    return {
        "epistemic_status": status.to_dict(),
        "hazards": hazards,
        "independent_signals": independent_signal_count(adjusted),
        "correlated_warnings": warnings,
        "cue_receipts": [r.to_dict() for r in receipts if r.active],
    }
