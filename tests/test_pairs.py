from meaning_assay import compare
from meaning_assay.cases import get as get_case


def test_kor_trinity_finding():
    p = compare(get_case("kor"), get_case("trinity"))
    assert p.significance_stable      # both weighty acts at a limit
    assert p.warrant_inverts          # positive -> negative
    assert p.finding == "significance holds, warrant inverts"


def test_quadrants_move_the_right_way():
    p = compare(get_case("kor"), get_case("trinity"))
    assert p.quadrant_a == "LUMINOUS"
    assert p.quadrant_b == "DANGEROUS"


def test_verdict_switchers_are_warrant_lenses():
    p = compare(get_case("kor"), get_case("trinity"))
    # Lenses that flip endorse->condemn between the cases.
    assert {"aristotelian", "buddhist", "relational", "stewardship", "confucian"} <= set(p.verdict_switchers)


def test_pair_is_order_sensitive_but_symmetric_in_magnitude():
    p1 = compare(get_case("kor"), get_case("trinity"))
    p2 = compare(get_case("trinity"), get_case("kor"))
    assert p1.warrant_inverts == p2.warrant_inverts
    assert p1.significance_delta == -p2.significance_delta
