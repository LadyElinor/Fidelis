from meaning_assay import render_case, render_pair_summary, compare
from meaning_assay.cases import get as get_case


def test_render_case_has_all_lenses():
    md = render_case(get_case("trinity"))
    assert md.startswith("# Trinity Across Twenty-Seven Traditions")
    # 27 second-level lens headers
    assert md.count("\n## ") == 28  # 27 lenses + "## Profile"
    assert "Quadrant: **DANGEROUS**" in md


def test_render_marks_provisional():
    md = render_case(get_case("kor"))
    # the outline-only readings should surface as provisional
    assert "Provisional readings" in md


def test_pair_summary_states_finding():
    md = render_pair_summary(compare(get_case("kor"), get_case("trinity")))
    assert "significance holds, warrant inverts" in md
