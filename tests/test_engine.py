import dataclasses

import pytest

from meaning_assay import analyze, validate, IntegrityError
from meaning_assay.cases import get as get_case
from meaning_assay.model import Reading, Grip, Polarity, Verdict


def test_cases_validate():
    validate(get_case("attest"))
    validate(get_case("kor"))
    validate(get_case("trinity"))
    validate(get_case("db_wipe"))
    validate(get_case("over_refusal"))
    validate(get_case("silent_policy_weaken"))


def test_kor_is_luminous():
    a = analyze(get_case("kor"))
    assert a.significance_high
    assert a.warrant is not None and a.warrant > 0
    assert a.quadrant == "LUMINOUS"


def test_trinity_is_dangerous():
    a = analyze(get_case("trinity"))
    assert a.significance_high            # a momentous act scores as significant
    assert a.warrant is not None and a.warrant < 0
    assert a.quadrant == "DANGEROUS"


def test_trinity_significance_comparable_to_kor():
    # Both are weighty acts at a limit; significance should not collapse for the atrocity.
    k = analyze(get_case("kor")).significance
    t = analyze(get_case("trinity")).significance
    assert abs(k - t) < 0.25


def test_warrant_lenses_carry_the_condemnation():
    a = analyze(get_case("trinity"))
    # Teleological/relational lenses do the condemning; agency lenses stay silent.
    condemning = set(a.warrant_lenses_condemning)
    assert {"aristotelian", "stewardship", "ecological_reciprocity", "emancipatory"} <= condemning
    assert "existential" not in condemning and "stoic" not in condemning


def test_attest_is_dangerous_and_self_certified():
    a = analyze(get_case("attest"))
    assert a.significance_high
    assert a.warrant is not None and a.warrant < 0
    assert a.quadrant == "DANGEROUS"
    assert "traditionalist" in a.self_certified_keys
    assert "stewardship" in a.repairs


def test_integrity_rejects_a_non_warrant_lens_that_judges():
    case = get_case("kor")
    # Mutate the existential (significance-only) reading to deliver a verdict.
    bad = []
    for r in case.readings:
        if r.tradition_key == "existential":
            r = dataclasses.replace(r, verdict=Verdict.ENDORSE)
        bad.append(r)
    broken = dataclasses.replace(case, readings=tuple(bad))
    with pytest.raises(IntegrityError):
        validate(broken)


def test_integrity_rejects_missing_reading():
    case = get_case("kor")
    short = dataclasses.replace(case, readings=case.readings[:-1])
    with pytest.raises(IntegrityError):
        validate(short)
