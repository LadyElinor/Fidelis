from meaning_assay import analyze
from meaning_assay.bridge import CouncilOutput, CouncilVerdict, reconcile, warrant_assay_record
from meaning_assay.cases import get as get_case


def test_db_wipe_is_under_justified_when_council_allows():
    case = get_case("db_wipe")
    analysis = analyze(case)
    result = reconcile(CouncilOutput(case.key, CouncilVerdict.ALLOW), analysis)
    assert result.alignment == "UNDER_JUSTIFIED"
    assert result.warranted_action == CouncilVerdict.REFUSE


def test_over_refusal_is_significance_driven_or_overreaction_when_council_refuses():
    case = get_case("over_refusal")
    analysis = analyze(case)
    result = reconcile(CouncilOutput(case.key, CouncilVerdict.REFUSE), analysis)
    assert result.alignment in {"OVER_REACTION", "SIGNIFICANCE_DRIVEN"}


def test_warrant_assay_record_is_deterministic_when_timestamp_fixed():
    case = get_case("silent_policy_weaken")
    council = CouncilOutput(case.key, CouncilVerdict.ALLOW)
    r1 = warrant_assay_record(case, council, timestamp="2026-06-06T16:00:00+00:00")
    r2 = warrant_assay_record(case, council, timestamp="2026-06-06T16:00:00+00:00")
    assert r1 == r2
    assert len(r1["record_sha256"]) == 64


def test_provisional_scenarios_surface_provisional_readings():
    case = get_case("db_wipe")
    record = warrant_assay_record(case, CouncilOutput(case.key, CouncilVerdict.REFUSE), timestamp="2026-06-06T16:00:00+00:00")
    assert record["provisional_readings"]
