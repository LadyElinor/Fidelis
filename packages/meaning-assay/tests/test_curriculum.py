"""Tests for the curriculum incorporations: twin tests, preserved dissent, ledger."""

import dataclasses

import pytest

from meaning_assay import analyze, validate
from meaning_assay.cases import get
from meaning_assay.engine import IntegrityError
from meaning_assay.model import Citation, Dissent, Grip, Polarity, Reading, Verdict
from meaning_assay.twins import TwinFinding, bright_twin_test, dark_twin_test
from meaning_assay import ledger


def _swap_all(case, **changes_by_key):
    readings = tuple(
        dataclasses.replace(r, **changes_by_key[r.tradition_key])
        if r.tradition_key in changes_by_key else r
        for r in case.readings
    )
    return dataclasses.replace(case, readings=readings)


# --- twins -------------------------------------------------------------------

def test_kor_dark_twin_validates_the_instrument():
    t = dark_twin_test(get("kor"), get("kor_dark"))
    assert t.finding is TwinFinding.INSTRUMENT_VALIDATED
    assert t.pair.warrant_inverts and t.pair.significance_stable


def test_dark_twin_that_keeps_warrant_convicts_the_axis():
    # A "twin" identical to the original keeps warrant by construction:
    # the detector must report MEASURING_ELEGANCE, not validation.
    fake_twin = dataclasses.replace(get("kor"), key="kor_fake_twin")
    t = dark_twin_test(get("kor"), fake_twin)
    assert t.finding is TwinFinding.MEASURING_ELEGANCE


def test_bright_twin_outscoring_original_convicts_the_axis():
    # Gild kor: upgrade its MIXED warrant verdicts to ENDORSE.
    gilded = _swap_all(
        get("kor"),
        traditionalist={"verdict": Verdict.ENDORSE},
        theistic={"verdict": Verdict.ENDORSE},
        emancipatory={"verdict": Verdict.ENDORSE, "failure_tripped": False},
    )
    gilded = dataclasses.replace(gilded, key="kor_gilded")
    t = bright_twin_test(get("kor"), gilded)
    assert t.finding is TwinFinding.MEASURING_SENTIMENT


def test_malformed_twin_is_void_not_failed():
    # Neutralize enough significance readings and the twin stops being a twin.
    keys = ["contemplative", "existential", "narrative", "nietzschean",
            "multiplicity", "civilizational", "stoic", "nondual"]
    drained = _swap_all(get("kor"), **{k: {"polarity": Polarity.NEUTRAL} for k in keys})
    drained = dataclasses.replace(drained, key="kor_drained")
    t = dark_twin_test(get("kor"), drained)
    assert t.finding is TwinFinding.NOT_A_STRUCTURAL_MATCH


# --- preserved dissent --------------------------------------------------------

def test_dissent_is_preserved_with_attribution_and_never_scored():
    base = analyze(get("kor_dark"))
    assert "aristotelian" in base.preserved_dissents
    analyst, verdict, rationale = base.preserved_dissents["aristotelian"][0]
    assert analyst == "habituation-optimist" and verdict == "mixed" and rationale
    # Strip the dissent: both axes must be unchanged, proving it never scored.
    stripped = _swap_all(get("kor_dark"), aristotelian={"dissents": ()})
    s = analyze(stripped)
    assert s.warrant == base.warrant and s.significance == base.significance


def test_dissent_obeys_the_warrant_integrity_rule():
    d = Dissent("rogue", Verdict.CONDEMN, "a judging dissent on a non-warrant lens")
    bad = _swap_all(get("kor"), narrative={"dissents": (d,)})
    with pytest.raises(IntegrityError, match="dissent"):
        validate(bad)


def test_dissent_enters_the_receipt():
    from meaning_assay.receipts import receipt, verify
    r = receipt(get("kor_dark"))
    assert r["outputs"]["dissent_keys"] == ["aristotelian"]
    assert verify(r)


# --- ledger -------------------------------------------------------------------

def test_ledger_appends_chains_and_reviews(tmp_path):
    p = tmp_path / "assays.jsonl"
    ledger.append(p, get("kor"), note="first assay")
    ledger.append(p, get("kor_dark"), note="the dark twin")
    revised = _swap_all(get("kor"), emancipatory={"failure_tripped": False})
    ledger.append(p, revised, note="revised after re-reading the speech")
    assert ledger.verify_chain(p) == []
    flags = ledger.review(p)
    assert [f.kind for f in flags] == ["REVISION"]
    assert flags[0].case_key == "kor"


def test_ledger_tampering_breaks_the_chain(tmp_path):
    p = tmp_path / "assays.jsonl"
    ledger.append(p, get("kor"))
    ledger.append(p, get("trinity"))
    lines = p.read_text().splitlines()
    lines[0] = lines[0].replace('"first assay"', '"rewritten past"').replace(
        '"note": ""', '"note": "rewritten past"')
    p.write_text("\n".join(lines) + "\n")
    kinds = {f.kind for f in ledger.verify_chain(p)}
    assert "BROKEN_RECEIPT" in kinds or "BROKEN_CHAIN" in kinds
