from __future__ import annotations

import json
from pathlib import Path

from examples.minimal_mcp_agent.demo import run_demo
from examples.minimal_mcp_agent.hash_utils import deterministic_hash
from examples.minimal_mcp_agent.sophron_ingest import validate_cer_export


def _read_jsonl(path: str):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, records):
    path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in records) + "\n", encoding="utf-8")


def test_good_export_passes(tmp_path):
    export_path = run_demo(output_dir=str(tmp_path), approve_confirmation=True)
    result = validate_cer_export(export_path)
    assert result["valid"] is True
    assert result["records_processed"] >= 6


def test_rejected_confirmation_blocks_but_validates(tmp_path):
    export_path = run_demo(output_dir=str(tmp_path), approve_confirmation=False)
    result = validate_cer_export(export_path)
    assert result["valid"] is True
    records = _read_jsonl(export_path)
    assert any(r["record_type"] == "external_action" and r["payload"].get("status") == "blocked" for r in records)


def test_bad_hash_fails(tmp_path):
    export_path = run_demo(output_dir=str(tmp_path), approve_confirmation=True)
    records = _read_jsonl(export_path)
    records[0]["payload"]["agent_name"] = "tampered_agent"
    broken_path = tmp_path / "bad_hash.jsonl"
    _write_jsonl(broken_path, records)
    result = validate_cer_export(str(broken_path))
    assert result["valid"] is False
    assert any("Provenance hash mismatch" in v for v in result["violations"])


def test_missing_payload_fails(tmp_path):
    export_path = run_demo(output_dir=str(tmp_path), approve_confirmation=True)
    records = _read_jsonl(export_path)
    del records[0]["payload"]
    broken_path = tmp_path / "missing_payload.jsonl"
    _write_jsonl(broken_path, records)
    result = validate_cer_export(str(broken_path))
    assert result["valid"] is False
    assert any("payload" in v.lower() for v in result["violations"])


def test_invalid_schema_fails(tmp_path):
    export_path = run_demo(output_dir=str(tmp_path), approve_confirmation=True)
    records = _read_jsonl(export_path)
    records[0]["schema_version"] = "9.9"
    broken_path = tmp_path / "bad_schema.jsonl"
    _write_jsonl(broken_path, records)
    result = validate_cer_export(str(broken_path))
    assert result["valid"] is False
    assert any("Schema version mismatch" in v for v in result["violations"])


def test_invalid_gate_decision_fails(tmp_path):
    export_path = run_demo(output_dir=str(tmp_path), approve_confirmation=True)
    records = _read_jsonl(export_path)
    for rec in records:
        if rec["record_type"] == "gate_check":
            rec["payload"]["decision"] = "maybe"
            rec["provenance_hash"] = deterministic_hash(rec["payload"])
            break
    broken_path = tmp_path / "bad_gate.jsonl"
    _write_jsonl(broken_path, records)
    result = validate_cer_export(str(broken_path))
    assert result["valid"] is False
    assert any("invalid gate decision" in v for v in result["violations"])


def test_escalation_without_confirmation_or_block_fails(tmp_path):
    export_path = run_demo(output_dir=str(tmp_path), approve_confirmation=True)
    records = [r for r in _read_jsonl(export_path) if r["record_type"] not in {"confirmation", "external_action"}]
    broken_path = tmp_path / "missing_confirmation.jsonl"
    _write_jsonl(broken_path, records)
    result = validate_cer_export(str(broken_path))
    assert result["valid"] is False
    assert any("escalation lacks confirmation" in v for v in result["violations"])
