from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

CANONICAL_JSON_VERSION = "canonical-json-v1"
VALID_RECORD_TYPES = {"metric_observation", "gate_outcome", "cohort_partition"}
REQUIRED_ENVELOPE_FIELDS = {
    "contract_version",
    "schema_version",
    "canonical_json_version",
    "run_id",
    "record_type",
    "export_timestamp",
    "provenance_hash",
    "payload",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def deterministic_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _valid_timestamp(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except Exception:
        return False


def validate_record(record: dict[str, Any], line_num: int) -> list[str]:
    violations: list[str] = []
    missing = REQUIRED_ENVELOPE_FIELDS - set(record.keys())
    if missing:
        violations.append(f"Line {line_num}: missing envelope fields {sorted(missing)}")

    extra = set(record.keys()) - REQUIRED_ENVELOPE_FIELDS
    if extra:
        violations.append(f"Line {line_num}: unexpected envelope fields {sorted(extra)}")

    if record.get("contract_version") != "0.1":
        violations.append(f"Line {line_num}: contract version mismatch")
    if record.get("schema_version") != "0.1":
        violations.append(f"Line {line_num}: schema version mismatch")
    if record.get("canonical_json_version") != CANONICAL_JSON_VERSION:
        violations.append(f"Line {line_num}: canonical JSON version mismatch")
    if record.get("record_type") not in VALID_RECORD_TYPES:
        violations.append(f"Line {line_num}: invalid record_type {record.get('record_type')}")
    if not isinstance(record.get("run_id"), str) or not record.get("run_id"):
        violations.append(f"Line {line_num}: invalid run_id")
    if not _valid_timestamp(str(record.get("export_timestamp", ""))):
        violations.append(f"Line {line_num}: invalid export_timestamp")

    payload = record.get("payload")
    if not isinstance(payload, dict) or not payload:
        violations.append(f"Line {line_num}: missing or invalid payload")
        return violations

    expected_hash = deterministic_hash(payload)
    if record.get("provenance_hash") != expected_hash:
        violations.append(f"Line {line_num}: provenance hash mismatch")

    record_type = record.get("record_type")
    if record_type == "metric_observation":
        for field in ("metric_name", "value"):
            if field not in payload:
                violations.append(f"Line {line_num}: metric_observation payload missing {field}")
    elif record_type == "gate_outcome":
        for field in ("gate", "decision", "confidence"):
            if field not in payload:
                violations.append(f"Line {line_num}: gate_outcome payload missing {field}")
    elif record_type == "cohort_partition":
        for field in ("cohort_name", "included_run_ids", "excluded_run_ids", "overlap_count"):
            if field not in payload:
                violations.append(f"Line {line_num}: cohort_partition payload missing {field}")

    return violations


def validate_export(export_path: str) -> dict[str, Any]:
    path = Path(export_path)
    if not path.exists():
        return {"valid": False, "records_processed": 0, "violations": [f"Missing export file: {export_path}"]}

    violations: list[str] = []
    processed = 0
    for line_num, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        processed += 1
        violations.extend(validate_record(record, line_num))

    return {
        "valid": len(violations) == 0,
        "records_processed": processed,
        "violations": violations,
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("export_path")
    args = parser.parse_args()
    result = validate_export(args.export_path)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
