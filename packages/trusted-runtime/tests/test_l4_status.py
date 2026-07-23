from trusted_runtime.l4_status import l4_status_interpretation


def test_l4_status_interpretation_maps_validated():
    assert l4_status_interpretation("VALIDATED") == "validated SOPHRON evidence is present and linked into the runtime trace"


def test_l4_status_interpretation_maps_failed():
    assert l4_status_interpretation("FAILED") == "the SOPHRON adapter failed; do not treat TAS-local evidence as SOPHRON validation"


def test_l4_status_interpretation_maps_calibrating():
    assert l4_status_interpretation("CALIBRATING") == "partial SOPHRON structure exists, but it remains advisory/calibrating rather than validated"


def test_l4_status_interpretation_maps_unavailable_and_unknown_to_unavailable_message():
    expected = "no validated or partial SOPHRON evidence is available; only non-SOPHRON closure signals may exist"
    assert l4_status_interpretation("UNAVAILABLE") == expected
    assert l4_status_interpretation("SOMETHING_ELSE") == expected
