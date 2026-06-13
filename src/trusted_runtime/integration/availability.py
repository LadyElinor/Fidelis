from __future__ import annotations

from trusted_runtime.integration.engine import (
    _CER_TELEMETRY_SRC,
    _ETHICS_COUNCIL_SRC,
    _MEANING_ASSAY_SRC,
    _SOPHRON_CER_SRC,
    analyze,
    efm_council,
    get_meaning_case,
    meaning_assay_receipt,
)


def ethics_council_available() -> bool:
    return _ETHICS_COUNCIL_SRC is not None and efm_council is not None


def meaning_assay_available() -> bool:
    return (
        analyze is not None
        and meaning_assay_receipt is not None
        and get_meaning_case is not None
    )


def trustworthy_agent_stack_available() -> bool:
    return _CER_TELEMETRY_SRC is not None


def sophron_cer_available() -> bool:
    return _SOPHRON_CER_SRC is not None


def real_telemetry_stack_available() -> bool:
    return trustworthy_agent_stack_available() and sophron_cer_available()
