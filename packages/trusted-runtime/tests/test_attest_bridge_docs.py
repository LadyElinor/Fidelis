from __future__ import annotations

from pathlib import Path


def test_attest_bridge_doc_states_real_path_and_non_crypto_boundary():
    doc_path = Path(__file__).resolve().parents[1] / "docs" / "ATTEST_BRIDGE.md"
    text = doc_path.read_text(encoding="utf-8")

    assert "real `AttestAgentConlang` import/wiring path now exists behind an availability gate" in text
    assert "real structural/profile verifier calls" in text
    assert "should not yet be overread as a strong cryptographic trust claim by itself" in text
    assert "replay-safe or wall-clock-stable verification semantics" in text
