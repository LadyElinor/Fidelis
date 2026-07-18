from __future__ import annotations


def l4_status_interpretation(validation_status: str) -> str:
    if validation_status == "VALIDATED":
        return "validated SOPHRON evidence is present and linked into the runtime trace"
    if validation_status == "FAILED":
        return "the SOPHRON adapter failed; do not treat TAS-local evidence as SOPHRON validation"
    if validation_status == "CALIBRATING":
        return "partial SOPHRON structure exists, but it remains advisory/calibrating rather than validated"
    return "no validated or partial SOPHRON evidence is available; only non-SOPHRON closure signals may exist"
