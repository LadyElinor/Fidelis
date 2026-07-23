from __future__ import annotations

from pathlib import Path


def test_all_real_docs_state_cer_verifier_provenance_boundary():
    docs_root = Path(__file__).resolve().parents[1] / "docs"

    setup_text = (docs_root / "ALL_REAL_SETUP.md").read_text(encoding="utf-8")
    contract_text = (docs_root / "ALL_REAL_PROFILE_CONTRACT.md").read_text(encoding="utf-8")
    ci_text = (docs_root / "CI_INTEGRATION_MATRIX.md").read_text(encoding="utf-8")

    assert "CER verifier provenance" in setup_text
    assert "signature_verifier_identity" in setup_text
    assert "do **not** by themselves prove" in setup_text

    assert "typed CER verifier provenance block" in contract_text
    assert "provenance evidence, not a substitute for a green semantic verifier result" in contract_text

    assert "CER verifier provenance block" in ci_text
    assert "which Attest verifier/config surface actually flowed into the CER-facing artifact" in ci_text
