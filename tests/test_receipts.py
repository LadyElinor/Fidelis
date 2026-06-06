import dataclasses

from meaning_assay import receipt, verify
from meaning_assay.cases import get as get_case
from meaning_assay.receipts import lensbook_digest, sha256


def test_receipt_is_deterministic():
    r1 = receipt(get_case("trinity"))
    r2 = receipt(get_case("trinity"))
    assert r1 == r2
    assert r1["receipt_sha256"] == r2["receipt_sha256"]


def test_receipt_verifies():
    r = receipt(get_case("kor"))
    assert verify(r)


def test_tampering_breaks_verification():
    r = receipt(get_case("kor"))
    r["outputs"]["quadrant"] = "DANGEROUS"  # lie about the result
    assert not verify(r)


def test_distinct_cases_have_distinct_case_hashes():
    rk = receipt(get_case("kor"))
    rt = receipt(get_case("trinity"))
    assert rk["inputs"]["case_sha256"] != rt["inputs"]["case_sha256"]
    # but they share the same lensbook
    assert rk["inputs"]["lensbook_sha256"] == rt["inputs"]["lensbook_sha256"]


def test_lensbook_digest_stable():
    assert lensbook_digest() == lensbook_digest()


def test_sha256_canonical_ordering():
    # key order must not change the hash
    assert sha256({"a": 1, "b": 2}) == sha256({"b": 2, "a": 1})
