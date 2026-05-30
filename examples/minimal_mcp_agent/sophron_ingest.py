"""Minimal SOPHRON-CER ingestion and invariant validation."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    from .cer_emitter import VALID_DECISIONS, VALID_GATES
    from .hash_utils import CANONICAL_JSON_VERSION, deterministic_hash
except ImportError:  # pragma: no cover
    from cer_emitter import VALID_DECISIONS, VALID_GATES
    from hash_utils import CANONICAL_JSON_VERSION, deterministic_hash

REQUIRED_ENVELOPE_FIELDS = {
    "contract_version",
    "schema_version",
    "canonical_json_version",
    "export_timestamp",
    "record_type",
    "run_id",
    "provenance_hash",
    "payload",
}
VALID_RECORD_TYPES = {"run", "hazard_map", "gate_check", "confirmation", "external_action", "data_issue"}


def _valid_timestamp(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except Exception:
        return False


def _validate_payload(record: Dict[str, Any], line_num: int) -> List[str]:
    violations: List[str] = []
    record_type = record.get("record_type")
    payload = record.get("payload")

    if not isinstance(payload, dict) or not payload:
        return [f"Line {line_num}: Missing or invalid payload"]

    if record_type == "run":
        for field in ("run_id", "started_at", "agent_name", "channel"):
            if field not in payload:
                violations.append(f"Line {line_num}: run payload missing {field}")

    elif record_type == "hazard_map":
        for field in ("hazard_map_id", "overall_risk", "convergences", "recommendation"):
            if field not in payload:
                violations.append(f"Line {line_num}: hazard_map payload missing {field}")
        if payload.get("overall_risk") not in {"low", "medium", "high"}:
            violations.append(f"Line {line_num}: invalid hazard overall_risk")

    elif record_type == "gate_check":
        required = ("gate_check_id", "step_id", "gate", "decision", "justification", "confidence", "created_at")
        for field in required:
            if field not in payload:
                violations.append(f"Line {line_num}: gate_check payload missing {field}")
        if payload.get("gate") not in VALID_GATES:
            violations.append(f"Line {line_num}: invalid gate {payload.get('gate')}")
        if payload.get("decision") not in VALID_DECISIONS:
            violations.append(f"Line {line_num}: invalid gate decision {payload.get('decision')}")
        confidence = payload.get("confidence")
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            violations.append(f"Line {line_num}: confidence outside [0,1]")

    elif record_type == "confirmation":
        for field in ("confirmation_id", "step_id", "scope", "confirmed", "created_at"):
            if field not in payload:
                violations.append(f"Line {line_num}: confirmation payload missing {field}")
        if not isinstance(payload.get("confirmed"), bool):
            violations.append(f"Line {line_num}: confirmation.confirmed must be boolean")

    elif record_type == "external_action":
        for field in ("external_action_id", "step_id", "action", "target", "status", "created_at"):
            if field not in payload:
                violations.append(f"Line {line_num}: external_action payload missing {field}")
        if payload.get("status") not in {"completed", "blocked", "failed", "simulated"}:
            violations.append(f"Line {line_num}: invalid external_action status")

    return violations


def _validate_cross_record_invariants(records: List[Dict[str, Any]]) -> List[str]:
    violations: List[str] = []
    escalated_steps = set()
    confirmed_steps = set()
    blocked_steps = set()

    for record in records:
        payload = record["payload"]
        if record["record_type"] == "gate_check" and payload.get("decision") == "escalate":
            escalated_steps.add(payload.get("step_id"))
        if record["record_type"] == "confirmation" and payload.get("confirmed") is True:
            confirmed_steps.add(payload.get("step_id"))
        if record["record_type"] == "external_action" and payload.get("status") == "blocked":
            blocked_steps.add(payload.get("step_id"))

    for step_id in escalated_steps:
        if step_id not in confirmed_steps and step_id not in blocked_steps:
            violations.append(f"Step {step_id}: escalation lacks confirmation or blocked action record")

    return violations


def validate_cer_export(export_path: str) -> Dict[str, Any]:
    violations: List[str] = []
    records: List[Dict[str, Any]] = []
    path = Path(export_path)

    if not path.exists():
        return {"valid": False, "records_processed": 0, "violations": [f"Missing export file: {export_path}"], "summary": "File not found"}

    with path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                violations.append(f"Line {line_num}: Invalid JSON - {exc}")
                continue

            missing = REQUIRED_ENVELOPE_FIELDS - set(record.keys())
            if missing:
                violations.append(f"Line {line_num}: Missing envelope fields {sorted(missing)}")

            extra = set(record.keys()) - REQUIRED_ENVELOPE_FIELDS
            if extra:
                violations.append(f"Line {line_num}: Unexpected envelope fields {sorted(extra)}")

            if record.get("contract_version") != "0.1":
                violations.append(f"Line {line_num}: Contract version mismatch")
            if record.get("schema_version") != "0.1":
                violations.append(f"Line {line_num}: Schema version mismatch")
            if record.get("canonical_json_version") != CANONICAL_JSON_VERSION:
                violations.append(f"Line {line_num}: Canonical JSON version mismatch")
            if record.get("record_type") not in VALID_RECORD_TYPES:
                violations.append(f"Line {line_num}: Invalid record_type {record.get('record_type')}")
            if not isinstance(record.get("run_id"), str) or not record.get("run_id"):
                violations.append(f"Line {line_num}: Invalid run_id")
            if not _valid_timestamp(str(record.get("export_timestamp", ""))):
                violations.append(f"Line {line_num}: Invalid export_timestamp")

            payload = record.get("payload", {})
            if isinstance(payload, dict):
                expected_hash = deterministic_hash(payload)
                if record.get("provenance_hash") != expected_hash:
                    violations.append(f"Line {line_num}: Provenance hash mismatch")
            else:
                violations.append(f"Line {line_num}: Payload is not an object")

            violations.extend(_validate_payload(record, line_num))
            if isinstance(record.get("payload"), dict):
                records.append(record)

    violations.extend(_validate_cross_record_invariants(records))

    result = {
        "valid": len(violations) == 0,
        "records_processed": len(records),
        "violations": violations,
        "summary": f"Processed {len(records)} records. Violations: {len(violations)}",
    }
    print(f"[SOPHRON Validation] {result['summary']}")
    return result


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("export_path")
    args = parser.parse_args()
    result = validate_cer_export(args.export_path)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
