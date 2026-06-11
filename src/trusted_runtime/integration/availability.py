from __future__ import annotations

from trusted_runtime.integration.engine import _ETHICS_COUNCIL_SRC, _MEANING_ASSAY_SRC, efm_council, analyze, get_meaning_case, meaning_assay_receipt


def ethics_council_available() -> bool:
    return _ETHICS_COUNCIL_SRC is not None and efm_council is not None


def meaning_assay_available() -> bool:
    return (
        _MEANING_ASSAY_SRC is not None
        and analyze is not None
        and meaning_assay_receipt is not None
        and get_meaning_case is not None
    )
