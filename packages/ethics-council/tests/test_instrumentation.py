from __future__ import annotations

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from instrumentation import (
    CueFamilyRegistry,
    CueMatch,
    DetectorStatus,
    ConfidenceClass,
    EpistemicVerdict,
    LensReceipt,
    cue_match,
    primary_family,
    overlap_adjusted_signals,
    independent_signal_count,
    correlated_family_warnings,
    assess_prompt_thinness,
    assess_missing_context_burden,
    aggregate_detector_confidence,
    classify_epistemic_status,
    assemble_hazards,
    instrument_synthesis,
)


@pytest.fixture
def registry():
    config_path = Path(__file__).parent.parent / "config" / "cue_families.yaml"
    return CueFamilyRegistry.from_yaml(config_path)


def make_receipt(
    lens="virtue",
    status=DetectorStatus.MODERATE,
    confidence=ConfidenceClass.MEDIUM,
    trigger_cues=None,
    trigger_family="unclassified",
    missing_evidence=None,
    verdict="CAUTION",
    active=True,
):
    return LensReceipt(
        lens=lens,
        status=status,
        confidence=confidence,
        trigger_cues=trigger_cues or [],
        trigger_family=trigger_family,
        missing_evidence=missing_evidence or [],
        verdict=verdict,
        active=active,
    )


class TestCueMatch:
    def test_basic_match(self, registry):
        m = cue_match("This is urgent and we must act", ["urgent", "must"], registry)
        assert m.triggered
        assert "urgent" in m.matched_cues
        assert "must" in m.matched_cues
        assert "pressure_rationale" in m.families

    def test_no_match(self, registry):
        m = cue_match("Should we order pizza?", ["urgent", "catastrophic"], registry)
        assert not m.triggered
        assert m.matched_cues == []
        assert m.families == set()

    def test_truthy_drop_in_replacement(self, registry):
        m = cue_match("urgent action needed", ["urgent"], registry)
        if m:
            assert m.triggered

    def test_case_insensitive(self, registry):
        m = cue_match("URGENT decision", ["urgent"], registry)
        assert m.triggered

    def test_multiple_families(self, registry):
        m = cue_match("proceeded without explicit consent", ["without explicit consent"], registry)
        assert m.triggered
        assert "consent_violation" in m.families


class TestPrimaryFamily:
    def test_single_cue_returns_its_family(self, registry):
        fam = primary_family(["urgent"], registry)
        assert fam == "pressure_rationale"

    def test_multiple_cues_same_family(self, registry):
        fam = primary_family(["urgent", "must"], registry)
        assert fam == "pressure_rationale"

    def test_unclassified_cues(self, registry):
        fam = primary_family(["completely_unknown_phrase"], registry)
        assert fam == "unclassified"

    def test_empty_returns_unclassified(self, registry):
        fam = primary_family([], registry)
        assert fam == "unclassified"

    def test_tie_breaking_deterministic(self, registry):
        fam1 = primary_family(["urgent", "tracking"], registry)
        fam2 = primary_family(["tracking", "urgent"], registry)
        assert fam1 == fam2


class TestOverlapAdjustment:
    def test_three_detectors_same_family_collapse_to_one(self):
        receipts = [
            make_receipt(lens="virtue", trigger_family="efficiency_rationale"),
            make_receipt(lens="confucian", trigger_family="efficiency_rationale"),
            make_receipt(lens="institutional", trigger_family="efficiency_rationale"),
        ]
        adjusted = overlap_adjusted_signals(receipts)
        assert len(adjusted) == 1
        assert "efficiency_rationale" in adjusted
        assert len(adjusted["efficiency_rationale"]) == 3

    def test_independent_signal_count(self):
        receipts = [
            make_receipt(lens="virtue", trigger_family="efficiency_rationale"),
            make_receipt(lens="confucian", trigger_family="efficiency_rationale"),
            make_receipt(lens="kantian", trigger_family="consent_violation"),
        ]
        adjusted = overlap_adjusted_signals(receipts)
        assert independent_signal_count(adjusted) == 2

    def test_unclassified_preserved_as_independent(self):
        receipts = [
            make_receipt(lens="virtue", trigger_family="unclassified"),
            make_receipt(lens="confucian", trigger_family="unclassified"),
        ]
        adjusted = overlap_adjusted_signals(receipts)
        assert len(adjusted) == 2

    def test_inactive_excluded(self):
        receipts = [
            make_receipt(lens="virtue", trigger_family="efficiency_rationale", active=True),
            make_receipt(lens="stoic", trigger_family="efficiency_rationale", active=False,
                         status=DetectorStatus.INACTIVE),
        ]
        adjusted = overlap_adjusted_signals(receipts)
        assert len(adjusted["efficiency_rationale"]) == 1

    def test_correlated_warnings_at_threshold(self):
        receipts = [
            make_receipt(lens="virtue", trigger_family="efficiency_rationale"),
            make_receipt(lens="confucian", trigger_family="efficiency_rationale"),
            make_receipt(lens="institutional", trigger_family="efficiency_rationale"),
        ]
        adjusted = overlap_adjusted_signals(receipts)
        warnings = correlated_family_warnings(adjusted, min_detectors=3)
        assert len(warnings) == 1
        assert warnings[0]["family"] == "efficiency_rationale"
        assert warnings[0]["detector_count"] == 3

    def test_no_warning_below_threshold(self):
        receipts = [
            make_receipt(lens="virtue", trigger_family="efficiency_rationale"),
            make_receipt(lens="confucian", trigger_family="efficiency_rationale"),
        ]
        adjusted = overlap_adjusted_signals(receipts)
        warnings = correlated_family_warnings(adjusted, min_detectors=3)
        assert warnings == []


class TestPromptThinness:
    def test_thin_prompt(self):
        assert assess_prompt_thinness("Is it ethical?") == "thin"

    def test_concrete_prompt(self):
        prompt = "Our company wants to deploy a model that affects patients in our hospital."
        assert assess_prompt_thinness(prompt) == "concrete"

    def test_crisp_canonical_remains_at_least_moderate(self):
        prompt = "Should I pull the lever to save five workers by killing one?"
        assert assess_prompt_thinness(prompt) in ("moderate", "concrete")


class TestMissingContextBurden:
    def test_no_missing_evidence_low(self):
        receipts = [make_receipt(missing_evidence=[]) for _ in range(5)]
        assert assess_missing_context_burden(receipts) == "low"

    def test_many_missing_high(self):
        receipts = [make_receipt(missing_evidence=["q1", "q2", "q3"]) for _ in range(5)]
        assert assess_missing_context_burden(receipts) == "high"


class TestAggregateConfidence:
    def test_majority_high(self):
        receipts = [make_receipt(confidence=ConfidenceClass.HIGH) for _ in range(4)]
        receipts.append(make_receipt(confidence=ConfidenceClass.LOW))
        assert aggregate_detector_confidence(receipts) == ConfidenceClass.HIGH

    def test_majority_low(self):
        receipts = [make_receipt(confidence=ConfidenceClass.LOW) for _ in range(4)]
        receipts.append(make_receipt(confidence=ConfidenceClass.HIGH))
        assert aggregate_detector_confidence(receipts) == ConfidenceClass.LOW

    def test_mixed_medium(self):
        receipts = [
            make_receipt(confidence=ConfidenceClass.HIGH),
            make_receipt(confidence=ConfidenceClass.LOW),
            make_receipt(confidence=ConfidenceClass.MEDIUM),
        ]
        assert aggregate_detector_confidence(receipts) == ConfidenceClass.MEDIUM


class TestEpistemicStatus:
    def test_thin_prompt_high_missing_yields_suspend(self):
        receipts = [make_receipt(missing_evidence=["q1", "q2", "q3"]) for _ in range(5)]
        status = classify_epistemic_status("Is it ethical?", receipts)
        assert status.verdict == EpistemicVerdict.SUSPEND

    def test_suspension_required_yields_suspend(self):
        receipts = [make_receipt(confidence=ConfidenceClass.HIGH) for _ in range(5)]
        status = classify_epistemic_status(
            "Concrete prompt with deploy action and patient domain anchor.",
            receipts,
            suspension_required=True,
        )
        assert status.verdict == EpistemicVerdict.SUSPEND

    def test_impasse_yields_reviewable(self):
        receipts = [make_receipt(confidence=ConfidenceClass.HIGH) for _ in range(5)]
        status = classify_epistemic_status(
            "Concrete prompt about deploy decision for patient population in hospital.",
            receipts,
            impasse_present=True,
        )
        assert status.verdict == EpistemicVerdict.REVIEWABLE

    def test_concrete_high_confidence_yields_usable(self):
        receipts = [make_receipt(confidence=ConfidenceClass.HIGH, missing_evidence=[]) for _ in range(5)]
        status = classify_epistemic_status(
            "Our company wants to deploy a model affecting patients in our hospital.",
            receipts,
        )
        assert status.verdict == EpistemicVerdict.USABLE

    def test_low_confidence_yields_reviewable(self):
        receipts = [make_receipt(confidence=ConfidenceClass.LOW, missing_evidence=[]) for _ in range(5)]
        status = classify_epistemic_status(
            "Our company wants to deploy a model affecting patients.",
            receipts,
        )
        assert status.verdict == EpistemicVerdict.REVIEWABLE


class TestAssembleHazards:
    def test_family_grouping_in_hazards(self):
        receipts = [
            make_receipt(lens="virtue", trigger_family="efficiency_rationale", trigger_cues=["efficiency"]),
            make_receipt(lens="confucian", trigger_family="efficiency_rationale", trigger_cues=["throughput"]),
            make_receipt(lens="kantian", trigger_family="consent_violation", trigger_cues=["without explicit consent"]),
        ]
        hazards = assemble_hazards(receipts)
        assert len(hazards) == 2
        families = {h["trigger_family"] for h in hazards}
        assert families == {"efficiency_rationale", "consent_violation"}

    def test_cues_consolidated_in_hazard(self):
        receipts = [
            make_receipt(lens="virtue", trigger_family="efficiency_rationale", trigger_cues=["efficiency"]),
            make_receipt(lens="confucian", trigger_family="efficiency_rationale", trigger_cues=["throughput", "stakeholders"]),
        ]
        hazards = assemble_hazards(receipts)
        assert len(hazards) == 1
        cues = set(hazards[0]["trigger_cues"])
        assert {"efficiency", "throughput", "stakeholders"} <= cues


class TestInstrumentSynthesis:
    def test_full_payload_shape(self):
        receipts = [
            make_receipt(
                lens="kantian",
                status=DetectorStatus.STRONG,
                confidence=ConfidenceClass.HIGH,
                trigger_cues=["without explicit consent"],
                trigger_family="consent_violation",
                missing_evidence=["Was consent revocable?"],
                verdict="PROHIBIT",
            ),
            make_receipt(
                lens="institutional",
                status=DetectorStatus.STRONG,
                confidence=ConfidenceClass.HIGH,
                trigger_cues=["legal says the company is covered"],
                trigger_family="legal_cover_pattern",
                missing_evidence=["Who controls the data?"],
                verdict="PROHIBIT",
            ),
        ]
        result = instrument_synthesis(
            "Our app collects location data without explicit consent. Legal says the company is covered.",
            receipts,
            suspension_required=True,
        )

        assert "epistemic_status" in result
        assert "hazards" in result
        assert "independent_signals" in result
        assert "correlated_warnings" in result
        assert "cue_receipts" in result
        assert result["epistemic_status"]["verdict"] == "suspend"
        assert result["independent_signals"] == 2
        assert len(result["hazards"]) == 2
        assert result["correlated_warnings"] == []
        assert len(result["cue_receipts"]) == 2

    def test_correlated_detectors_warning(self):
        receipts = [
            make_receipt(lens="virtue", trigger_family="efficiency_rationale", trigger_cues=["efficiency"]),
            make_receipt(lens="confucian", trigger_family="efficiency_rationale", trigger_cues=["efficiency"]),
            make_receipt(lens="institutional", trigger_family="efficiency_rationale", trigger_cues=["efficiency"]),
        ]
        result = instrument_synthesis(
            "Should we restructure for efficiency in our hospital?",
            receipts,
        )

        assert result["independent_signals"] == 1
        assert len(result["correlated_warnings"]) == 1
        assert result["correlated_warnings"][0]["family"] == "efficiency_rationale"
        assert result["correlated_warnings"][0]["detector_count"] == 3
        assert result["epistemic_status"]["overlap_warning"] is True
