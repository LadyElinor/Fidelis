from __future__ import annotations

import json
from pathlib import Path

import pytest

from trusted_runtime.export import export_decision_payload
from trusted_runtime.integration.availability import (
    meaning_assay_available,
    real_telemetry_stack_available,
)
from trusted_runtime.integration.engine import assemble_execution_decision
from trusted_runtime.integration.formation import assess_formation_hazard
from trusted_runtime.l4_status import l4_status_interpretation
from trusted_runtime.shared.models import ProposedAction

FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "scenarios.json").read_text())
SCENARIOS = {k: v for k, v in FIXTURES.items() if not k.startswith("_")}

_ADAPTER_GATES = {"meaning_assay": meaning_assay_available}


def _decide(scenario):
    action = ProposedAction.model_validate(scenario["input"])
    return action, assemble_execution_decision(action)


def _families(decision):
    return sorted({h.split("::")[0] for h in decision.council.hazards if "::" in h})


@pytest.mark.parametrize("name", SCENARIOS.keys())
def test_env_independent_contract_holds(name):
    """Assertions in this tier must hold on a fresh clone with no sibling
    repos present. Anything requiring a REAL adapter belongs in the
    adapter_dependent tier, not here."""
    scenario = SCENARIOS[name]
    ei = scenario["contract"]["env_independent"]
    _, d = _decide(scenario)

    if "formation_families_present" in ei:
        present = [f for f in _families(d) if f == "formation"]
        assert present == ei["formation_families_present"]
    if "formation_hazards_required" in ei:
        haz = set(d.council.hazards)
        for required in ei["formation_hazards_required"]:
            assert required in haz
    if ei.get("claimed_provenance_is_ignored"):
        # An input claiming ALL_REAL provenance must never have that claim
        # echoed into process provenance, on any adapter tier.
        claimed = scenario["input"]["context"].get("claimed_provenance")
        assert claimed == "ALL_REAL"
        assert "claimed_provenance" not in d.process_provenance.get("warrant", {})
    if ei.get("warrant_translation_contested"):
        assert d.warrant is not None
        assert d.warrant.contested is True
    if expected_fit := ei.get("warrant_translation_fit_quality"):
        assert d.warrant is not None and d.warrant.pair_contrasts is not None
        assert d.warrant.pair_contrasts.get("translation_fit_quality") == expected_fit
    if note_fragment := ei.get("warrant_confidence_note_contains"):
        assert d.warrant is not None
        assert any(note_fragment in note for note in d.warrant.confidence_notes)
    if question_fragment := ei.get("warrant_unresolved_question_contains"):
        assert d.warrant is not None
        assert any(question_fragment in q for q in d.warrant.unresolved_questions)
    if ei.get("assert_l4_interpretation_matches_status"):
        payload = export_decision_payload(d)
        expected_l4_interpretation = l4_status_interpretation(payload["cer_bundle"]["sophron_validation"]["validation_status"])
        assert payload["l4_interpretation"] == expected_l4_interpretation
        assert payload["cer_bundle"]["sophron_validation"]["interpretation"] == expected_l4_interpretation


@pytest.mark.parametrize("name", [k for k, v in SCENARIOS.items() if "adapter_dependent" in v["contract"]])
def test_adapter_dependent_contract_holds(name):
    """REAL-provenance and real-adapter output assertions. Skips, with the
    missing dependency named, when the required sibling repo is absent —
    a skip is an honest receipt; a pass against a stub is not."""
    scenario = SCENARIOS[name]
    ad = scenario["contract"]["adapter_dependent"]
    required = ad["requires"]
    gate = _ADAPTER_GATES[required]
    if not gate():
        pytest.skip(f"{name}: sibling dependency '{required}' absent; REAL-adapter contract recorded but not asserted")

    _, d = _decide(scenario)
    if "warrant_provenance" in ad:
        assert d.warrant.adapter_provenance.value == ad["warrant_provenance"]
    if "warrant_quadrant" in ad:
        assert d.warrant.normative_summary.value == ad["warrant_quadrant"]
    if ad.get("warrant_band_negative"):
        assert d.warrant.warrant is not None and d.warrant.warrant < 0
    if ad.get("claimed_provenance_is_not_trusted"):
        claimed = scenario["input"]["context"].get("claimed_provenance")
        assert claimed == "ALL_REAL"
        assert d.adapter_provenance["warrant"].value == "REAL"
        assert "claimed_provenance" not in d.process_provenance.get("warrant", {})


@pytest.mark.parametrize("name", SCENARIOS.keys())
def test_overall_receipt_is_deterministic(name):
    scenario = SCENARIOS[name]
    if not scenario["contract"]["env_independent"].get("deterministic_overall_receipt"):
        pytest.skip("fixture does not assert determinism")
    _, d1 = _decide(scenario)
    _, d2 = _decide(scenario)
    assert d1.overall_receipt.sha256 == d2.overall_receipt.sha256


def _formation_lens_hash(description: str, context: dict) -> str:
    """Canonical hash of the formation LENS output, pure logic and environment-independent.
    The full decision receipt is not pinned here because formation_event routes through
    the council layer, which may be STUB without sibling repos."""
    import hashlib

    r = assess_formation_hazard(description, context)
    payload = {
        "is_formation_event": r.is_formation_event,
        "is_canonization_event": r.is_canonization_event,
        "hazards": sorted(r.hazards),
        "matched_kind": r.matched_kind,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


@pytest.mark.parametrize("name", [k for k, v in SCENARIOS.items() if v["contract"]["env_independent"].get("formation_lens_golden_sha256")])
def test_pinned_formation_lens_golden(name):
    scenario = SCENARIOS[name]
    actual = _formation_lens_hash(scenario["input"]["description"], scenario["input"]["context"])
    assert actual == scenario["contract"]["env_independent"]["formation_lens_golden_sha256"]


FORMATION_GOLDEN_INPUT = {
    "id": "fixture-formation-golden",
    "timestamp": "2026-06-12T00:00:00+00:00",
    "description": "Ingest a training corpus selected to shape model behavior.",
    "context": {"change_type": "training_corpus", "meaning_case_key": "kor"},
    "proposed_by": "agent-session",
}


def test_formation_lens_golden_behavior():
    r = assess_formation_hazard(FORMATION_GOLDEN_INPUT["description"], FORMATION_GOLDEN_INPUT["context"])
    assert r.is_formation_event and r.is_canonization_event
    assert set(r.hazards) == {
        "formation::scale_without_consent",
        "formation::canonization_power",
        "formation::replication_blind_canon",
        "formation::amplified_under_depletion",
        "formation::no_correction_loop",
    }
    assert r.matched_kind == "training_corpus"


@pytest.mark.parametrize("name", SCENARIOS.keys())
def test_structural_tier_is_well_formed(name):
    scenario = SCENARIOS[name]
    ed = scenario["contract"]["env_dependent_structural"]
    _, d = _decide(scenario)

    assert d.decision_integrity.value in ed["decision_integrity_in"]

    if not real_telemetry_stack_available():
        pytest.skip(f"{name}: real stack absent; full-integrity contract recorded but not asserted")

    expected = ed.get("expected_when_full", {})
    if expected.get("runtime_disposition"):
        assert d.runtime_disposition.value == expected["runtime_disposition"]
    if expected.get("runtime_disposition_not"):
        assert d.runtime_disposition.value != expected["runtime_disposition_not"]
    if expected.get("reconciliation_alignment"):
        recon = d.model_dump(mode="json").get("reconciliation") or {}
        assert recon.get("alignment") == expected["reconciliation_alignment"]
    if expected.get("hazard_unclassified_count") is not None:
        assert d.hazard_profile.get("unclassified_count") == expected["hazard_unclassified_count"]
    if expected_family := expected.get("hazard_family_present"):
        assert expected_family in d.hazard_profile.get("families_present", [])


def test_fixture_inputs_all_validate():
    for scenario in SCENARIOS.values():
        ProposedAction.model_validate(scenario["input"])
