from __future__ import annotations

from pathlib import Path

from ethics import care, kantian, stoic
from meaning import assay
from telemetry import checks, vector
from runtime.loader import InputValidationRuntimeError, load_and_validate
from runtime.models import RuntimeDecisionResult
from runtime.receipts import write_all_receipts


def run_case(path: str) -> dict:
    input_path = Path(path)

    try:
        case = load_and_validate(input_path)
    except InputValidationRuntimeError:
        raise

    lens_results = [
        kantian.evaluate(case),
        stoic.evaluate(case),
        care.evaluate(case),
    ]
    meaning_result = assay.evaluate(case, lens_results)
    telemetry_vector = vector.compute(case, lens_results, meaning_result)
    telemetry_flags = checks.evaluate(telemetry_vector)

    from runtime.gating import decide

    decision: RuntimeDecisionResult = decide(
        case=case,
        lens_results=lens_results,
        meaning=meaning_result,
        telemetry_vector=telemetry_vector,
        telemetry_flags=telemetry_flags,
    )

    receipts_info = write_all_receipts(
        base_dir=input_path.parent.parent / "receipts",
        case_payload=case.model_dump(),
        lens_results=[item.model_dump() for item in lens_results],
        meaning_payload=meaning_result.model_dump(),
        telemetry_payload={
            "vector": telemetry_vector.model_dump(),
            "flags": telemetry_flags,
        },
        decision=decision,
    )

    decision.receipt_hash = receipts_info["decision_hash"]

    return {
        **decision.model_dump(),
        "artifacts_dir": receipts_info["artifacts_dir"],
        "final_chain_hash": receipts_info["final_chain_hash"],
    }
