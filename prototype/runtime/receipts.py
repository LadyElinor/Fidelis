from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.hashing import sha256_json
from runtime.models import RuntimeDecisionResult


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_all_receipts(
    base_dir: str | Path,
    case_payload: dict[str, Any],
    lens_results: list[dict[str, Any]],
    meaning_payload: dict[str, Any],
    telemetry_payload: dict[str, Any],
    decision: RuntimeDecisionResult,
) -> dict[str, str]:
    case_id = case_payload["case_id"]
    out_dir = Path(base_dir) / case_id
    out_dir.mkdir(parents=True, exist_ok=True)

    input_payload = {"case_id": case_id, "input": case_payload}
    input_payload["hash"] = sha256_json(input_payload)
    _write_json(out_dir / "input.json", input_payload)

    ethics_payload = {"case_id": case_id, "lenses": lens_results}
    ethics_payload["hash"] = sha256_json(ethics_payload)
    _write_json(out_dir / "ethics_council.json", ethics_payload)

    meaning_body = {"case_id": case_id, **meaning_payload}
    meaning_body["hash"] = sha256_json(meaning_body)
    _write_json(out_dir / "meaning_assay.json", meaning_body)

    telemetry_body = {"case_id": case_id, **telemetry_payload}
    telemetry_body["hash"] = sha256_json(telemetry_body)
    _write_json(out_dir / "telemetry.json", telemetry_body)

    parent_receipts = [input_payload["hash"], ethics_payload["hash"], meaning_body["hash"], telemetry_body["hash"]]
    decision_payload = decision.model_dump()
    decision_payload["parent_receipts"] = parent_receipts
    decision_payload["hash"] = sha256_json(decision_payload)
    _write_json(out_dir / "runtime_decision.json", decision_payload)

    receipt_chain = {
        "case_id": case_id,
        "artifacts": {
            "input": input_payload["hash"],
            "ethics": ethics_payload["hash"],
            "meaning": meaning_body["hash"],
            "telemetry": telemetry_body["hash"],
            "decision": decision_payload["hash"],
        },
    }
    receipt_chain["final_chain_hash"] = sha256_json(receipt_chain)
    _write_json(out_dir / "receipt_chain.json", receipt_chain)

    return {
        "artifacts_dir": str(out_dir),
        "decision_hash": decision_payload["hash"],
        "final_chain_hash": receipt_chain["final_chain_hash"],
    }
