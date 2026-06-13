from datetime import datetime, timezone

from trusted_runtime.integration.engine import assemble_execution_decision
from trusted_runtime.integration.formation import FormationHazardReport, assess_formation_hazard
from trusted_runtime.shared.models import ProposedAction


FIXED_TS = datetime(2026, 6, 12, tzinfo=timezone.utc)


def _action(description: str, **context):
    return ProposedAction(
        id="formation-test",
        timestamp=FIXED_TS,
        description=description,
        context=context,
    )


def test_declared_training_corpus_is_a_canonization_event():
    r = assess_formation_hazard("ingest data", {"change_type": "training_corpus"})
    assert r.is_formation_event and r.is_canonization_event
    assert "formation::scale_without_consent" in r.hazards
    assert "formation::canonization_power" in r.hazards
    assert "formation::replication_blind_canon" in r.hazards
    assert r.matched_kind == "training_corpus"


def test_recommender_is_formation_and_canonization():
    r = assess_formation_hazard("ship a new feed ranking model", {})
    assert r.is_formation_event and r.is_canonization_event


def test_generated_media_release_forms_without_canonizing():
    r = assess_formation_hazard("release", {"change_type": "generated_media_release"})
    assert r.is_formation_event and not r.is_canonization_event
    assert "formation::canonization_power" not in r.hazards
    assert "formation::amplified_under_depletion" in r.hazards
    assert "formation::no_correction_loop" in r.hazards


def test_ordinary_action_does_not_fire():
    r = assess_formation_hazard("fix an off-by-one in pagination", {"change_type": "bugfix"})
    assert r == FormationHazardReport(False, False, rationale=r.rationale)
    assert not r.hazards


def test_phrase_fallback_when_no_declared_kind():
    r = assess_formation_hazard("update the course curriculum for next term", {})
    assert r.is_formation_event
    assert r.matched_kind is None and r.matched_phrase == "curriculum"


def test_formation_hazards_merge_into_council_assessment():
    d = assemble_execution_decision(
        _action("ingest a training corpus to shape model behavior", change_type="training_corpus")
    )
    formation = [h for h in d.council.hazards if h.startswith("formation::")]
    assert "formation::scale_without_consent" in formation
    assert any(n.startswith("formation lens:") for n in d.council.confidence_notes)


def test_merge_is_additive_not_replacing():
    d = assemble_execution_decision(
        _action("tighten safety-critical invariant handling", change_type="safety_invariant")
    )
    assert d.council.hazards
    assert not [h for h in d.council.hazards if h.startswith("formation::")]


def test_formation_merge_preserves_determinism():
    a = _action("ship a recommender ranking change", change_type="ranking_change")
    d1 = assemble_execution_decision(a)
    d2 = assemble_execution_decision(a)
    assert d1.overall_receipt.sha256 == d2.overall_receipt.sha256
