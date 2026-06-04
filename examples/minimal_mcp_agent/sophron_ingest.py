"""Minimal SOPHRON-CER ingestion and invariant validation."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

try:
    from .cer_emitter import VALID_DECISIONS, VALID_GATES
    from .hash_utils import CANONICAL_JSON_VERSION, DEFAULT_SIGNING_KEY_ID, deterministic_hash, verify_signature
except ImportError:  # pragma: no cover
    from cer_emitter import VALID_DECISIONS, VALID_GATES
    from hash_utils import CANONICAL_JSON_VERSION, DEFAULT_SIGNING_KEY_ID, deterministic_hash, verify_signature

REQUIRED_ENVELOPE_FIELDS = {
    "contract_version",
    "schema_version",
    "canonical_json_version",
    "export_timestamp",
    "record_type",
    "run_id",
    "provenance_hash",
    "signature",
    "signature_algorithm",
    "signing_key_id",
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
        for field in (
            "confirmation_id",
            "step_id",
            "scope",
            "reason",
            "confirmed",
            "requested_by_gate",
            "requested_action",
            "requested_target",
            "created_at",
        ):
            if field not in payload:
                violations.append(f"Line {line_num}: confirmation payload missing {field}")
        if not isinstance(payload.get("confirmed"), bool):
            violations.append(f"Line {line_num}: confirmation.confirmed must be boolean")
        if payload.get("requested_by_gate") is not None and payload.get("requested_by_gate") not in VALID_GATES:
            violations.append(f"Line {line_num}: confirmation requested_by_gate is invalid")

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
    escalated_gates_by_step: Dict[str, set[str]] = {}
    confirmation_by_step: Dict[str, Dict[str, Any]] = {}
    external_action_by_step: Dict[str, Dict[str, Any]] = {}

    for index, record in enumerate(records):
        payload = record["payload"]
        step_id = payload.get("step_id")
        if record["record_type"] == "gate_check" and payload.get("decision") == "escalate":
            escalated_steps.add(step_id)
            escalated_gates_by_step.setdefault(step_id, set()).add(payload.get("gate"))
        if record["record_type"] == "confirmation":
            confirmation_by_step[step_id] = {"index": index, "payload": payload}
            if payload.get("confirmed") is True:
                confirmed_steps.add(step_id)
        if record["record_type"] == "external_action":
            external_action_by_step[step_id] = {"index": index, "payload": payload}
            if payload.get("status") == "blocked":
                blocked_steps.add(step_id)

    for step_id in escalated_steps:
        if step_id not in confirmed_steps and step_id not in blocked_steps:
            violations.append(f"Step {step_id}: escalation lacks confirmation or blocked action record")

        confirmation = confirmation_by_step.get(step_id)
        action_record = external_action_by_step.get(step_id)
        gates = escalated_gates_by_step.get(step_id, set())

        if confirmation:
            requested_gate = confirmation["payload"].get("requested_by_gate")
            if requested_gate is not None and requested_gate not in gates:
                violations.append(f"Step {step_id}: confirmation gate linkage does not match escalated gates")
            if action_record and confirmation["index"] > action_record["index"]:
                violations.append(f"Step {step_id}: confirmation appears after external action record")
            requested_action = confirmation["payload"].get("requested_action")
            requested_target = confirmation["payload"].get("requested_target")
            if action_record:
                if requested_action and requested_action != action_record["payload"].get("action"):
                    violations.append(f"Step {step_id}: confirmation requested_action does not match external action")
                if requested_target and requested_target != action_record["payload"].get("target"):
                    violations.append(f"Step {step_id}: confirmation requested_target does not match external action")

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
            if record.get("signature_algorithm") != "hmac-sha256":
                violations.append(f"Line {line_num}: Unsupported signature_algorithm")
            if record.get("signing_key_id") != DEFAULT_SIGNING_KEY_ID:
                violations.append(f"Line {line_num}: Unknown signing_key_id")

            payload = record.get("payload", {})
            if isinstance(payload, dict):
                expected_hash = deterministic_hash(payload)
                if record.get("provenance_hash") != expected_hash:
                    violations.append(f"Line {line_num}: Provenance hash mismatch")
                if not verify_signature(payload, str(record.get("signature", ""))):
                    violations.append(f"Line {line_num}: Signature verification failed")
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
