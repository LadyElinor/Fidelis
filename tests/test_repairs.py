import dataclasses

import pytest

from meaning_assay.cases import get as get_case
from meaning_assay.engine import IntegrityError, analyze, validate
from meaning_assay.model import Citation, Grip, Polarity, Reading, Verdict
from meaning_assay.pairs import compare
from meaning_assay.receipts import _case_fingerprint, receipt, sha256, verify

KOR_PRISTINE_HASH = "ab1ccecd5dedfb74"


def _swap(case, key, **changes):
    readings = tuple(
        dataclasses.replace(r, **changes) if r.tradition_key == key else r
        for r in case.readings
    )
    return dataclasses.replace(case, readings=readings)


def test_repair_forbidden_on_non_warrant_lens():
    bad = _swap(get_case("kor"), "existential", repair="x")
    with pytest.raises(IntegrityError, match="non-WARRANT"):
        validate(bad)


def test_repair_forbidden_on_endorse_verdict():
    bad = _swap(get_case("kor"), "aristotelian", repair="x")
    with pytest.raises(IntegrityError, match="repair"):
        validate(bad)


def test_repair_allowed_and_surfaced_on_condemn_and_mixed():
    case = _swap(get_case("kor"), "emancipatory", repair="forgive without proposing amnesty")
    a = analyze(case)
    assert a.repairs == {"emancipatory": "forgive without proposing amnesty"}


def test_self_report_is_provisional_and_flagged():
    r = Reading("stoic", Grip.PARTIAL, Polarity.AFFIRMS, False, Verdict.NA,
                "n", (Citation("self_report", "the agent's own account"),))
    assert r.provisional
    assert r.self_certified
    mixed = Reading("stoic", Grip.PARTIAL, Polarity.AFFIRMS, False, Verdict.NA,
                    "n", (Citation("self_report", "agent"), Citation("scholarly", "lit")))
    assert not mixed.provisional and not mixed.self_certified


def test_legacy_case_hashes_unchanged():
    assert sha256(_case_fingerprint(get_case("kor")))[:16] == KOR_PRISTINE_HASH


def test_receipt_with_repairs_verifies_and_changes_case_hash():
    base = get_case("kor")
    repaired = _swap(base, "emancipatory", repair="forgive without proposing amnesty")
    assert sha256(_case_fingerprint(base)) != sha256(_case_fingerprint(repaired))
    assert verify(receipt(repaired))


def test_pair_textures_populated():
    p = compare(get_case("kor"), get_case("trinity"))
    assert p.texture_a in {"focal", "diffuse", "mixed", "clean"}
    assert p.texture_b in {"focal", "diffuse", "mixed", "clean"}
    assert isinstance(p.trips_shared, tuple)
