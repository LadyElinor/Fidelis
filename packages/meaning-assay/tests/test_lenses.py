from meaning_assay.lenses import LENSBOOK, BY_KEY
from meaning_assay.model import Function


def test_twenty_seven_lenses():
    assert len(LENSBOOK) == 27


def test_keys_unique():
    keys = [t.key for t in LENSBOOK]
    assert len(keys) == len(set(keys))


def test_numerals_unique_and_complete():
    nums = [t.numeral for t in LENSBOOK]
    assert len(nums) == len(set(nums)) == 27


def test_every_tradition_has_rationale():
    for t in LENSBOOK:
        assert t.function_rationale.strip()


def test_exactly_one_null_lens_is_nihilist():
    nulls = [t for t in LENSBOOK if t.is_null]
    assert len(nulls) == 1
    assert nulls[0].key == "nihilist"


def test_function_distribution():
    warrant = [t for t in LENSBOOK if t.does(Function.WARRANT)]
    sig_only = [t for t in LENSBOOK if t.functions == frozenset({Function.SIGNIFICANCE})]
    mechanism_no_warrant = [
        t for t in LENSBOOK
        if t.does(Function.MECHANISM) and not t.does(Function.WARRANT)
    ]
    # The split is the whole point: a bloc that can judge, a bloc that only locates
    # significance, and a bloc that only describes a mechanism.
    assert len(warrant) == 12
    assert len(sig_only) == 6      # contemplative, existential, nietzschean, nondual, stoic, erotic
    assert len(mechanism_no_warrant) == 8
    assert len(warrant) + len(sig_only) + len(mechanism_no_warrant) + 1 == 27  # +1 null (nihilist)


def test_agency_lenses_cannot_judge():
    # Existential, Stoic, Nietzschean locate significance but carry no act-warrant.
    for key in ("existential", "stoic", "nietzschean"):
        assert not BY_KEY[key].does(Function.WARRANT)
