from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import IntEnum
from typing import Any

from .engine import Analysis, analyze
from .model import Case
from .receipts import receipt as case_receipt


class CouncilVerdict(IntEnum):
    ALLOW = 0
    REVIEW = 1
    ESCALATE = 2
    REFUSE = 3


@dataclass(frozen=True)
class CouncilOutput:
    case_key: str
    verdict: CouncilVerdict


@dataclass(frozen=True)
class Reconciliation:
    case_key: str
    council_verdict: CouncilVerdict
    warranted_action: CouncilVerdict
    alignment: str
    rationale: str


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _sha256(obj: Any) -> str:
    return hashlib.sha256(_canonical(obj).encode("utf-8")).hexdigest()


def warranted_action_for(analysis: Analysis) -> CouncilVerdict:
    if analysis.warrant_band == "negative":
        return CouncilVerdict.REFUSE
    if analysis.warrant_band == "positive":
        return CouncilVerdict.ALLOW
    if analysis.warrant_band == "contested":
        return CouncilVerdict.REVIEW
    return CouncilVerdict.REVIEW


def reconcile(council: CouncilOutput, analysis: Analysis) -> Reconciliation:
    warranted = warranted_action_for(analysis)

    if council.verdict == warranted:
        alignment = "ALIGNED"
    elif council.verdict > warranted:
        if analysis.significance_high and analysis.warrant_band != "negative":
            alignment = "SIGNIFICANCE_DRIVEN"
        else:
            alignment = "OVER_REACTION"
    else:
        alignment = "UNDER_JUSTIFIED"

    rationale = (
        f"Council chose {council.verdict.name}; warrant layer recommends {warranted.name} "
        f"from quadrant={analysis.quadrant}, warrant_band={analysis.warrant_band}."
    )
    return Reconciliation(
        case_key=analysis.case_key,
        council_verdict=council.verdict,
        warranted_action=warranted,
        alignment=alignment,
        rationale=rationale,
    )


def warrant_assay_record(
    case: Case,
    council: CouncilOutput,
    *,
    step_id: str = "step_001",
    assay_id: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    analysis = analyze(case)
    reconciliation = reconcile(council, analysis)
    source = case_receipt(case)

    assay_id = assay_id or f"wa_{case.key}"
    payload = {
        "assay_id": assay_id,
        "step_id": step_id,
        "case_key": case.key,
        "quadrant": analysis.quadrant,
        "warrant_band": analysis.warrant_band,
        "warranted_action": reconciliation.warranted_action.name,
        "alignment": reconciliation.alignment,
        "significance": analysis.significance,
        "warrant": analysis.warrant,
        "failure_trip_rate": analysis.failure_trip_rate,
        "warrant_condemning": list(analysis.warrant_lenses_condemning),
        "provisional_readings": list(analysis.provisional_keys),
        "source_receipt_sha256": source["receipt_sha256"],
        "created_at": timestamp,
    }
    payload["record_sha256"] = _sha256(payload)
    return payload
