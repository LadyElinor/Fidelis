from runtime.hashing import sha256_json


def test_key_order_does_not_change_hash() -> None:
    a = {"x": 1, "y": 2}
    b = {"y": 2, "x": 1}
    assert sha256_json(a) == sha256_json(b)
