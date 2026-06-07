from __future__ import annotations

import json
from pathlib import Path

from examples.minimal_mcp_agent.demo import run_demo
from examples.minimal_mcp_agent.hash_utils import deterministic_hash, sign_payload
from examples.minimal_mcp_agent.sophron_ingest import validate_cer_export


def _read_jsonl(path: str):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, records):
    path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in records) + "\n", encoding="utf-8")


def test_good_export_passes(tmp_path):
    export_path = run_demo(output_dir=str(tmp_path), approve_confirmation=True)
    result = validate_cer_export(export_path)
    assert result["valid"] is True
    assert result["records_processed"] >= 9


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


def test_bad_signature_fails(tmp_path):
    export_path = run_demo(output_dir=str(tmp_path), approve_confirmation=True)
    records = _read_jsonl(export_path)
    records[0]["signature"] = "0" * 64
    broken_path = tmp_path / "bad_signature.jsonl"
    _write_jsonl(broken_path, records)
    result = validate_cer_export(str(broken_path))
    assert result["valid"] is False
    assert any("Signature verification failed" in v for v in result["violations"])


def test_unknown_signing_key_fails(tmp_path):
    export_path = run_demo(output_dir=str(tmp_path), approve_confirmation=True)
    records = _read_jsonl(export_path)
    records[0]["signing_key_id"] = "unknown-key"
    broken_path = tmp_path / "bad_key.jsonl"
    _write_jsonl(broken_path, records)
    result = validate_cer_export(str(broken_path))
    assert result["valid"] is False
    assert any("Unknown signing_key_id" in v for v in result["violations"])


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


def test_confirmation_gate_linkage_mismatch_fails(tmp_path):
    export_path = run_demo(output_dir=str(tmp_path), approve_confirmation=True)
    records = _read_jsonl(export_path)
    for rec in records:
        if rec["record_type"] == "confirmation":
            rec["payload"]["requested_by_gate"] = "least_privilege"
            rec["provenance_hash"] = deterministic_hash(rec["payload"])
            break
    broken_path = tmp_path / "bad_confirmation_gate.jsonl"
    _write_jsonl(broken_path, records)
    result = validate_cer_export(str(broken_path))
    assert result["valid"] is False
    assert any("gate linkage" in v for v in result["violations"])


def test_confirmation_after_external_action_fails(tmp_path):
    export_path = run_demo(output_dir=str(tmp_path), approve_confirmation=True)
    records = _read_jsonl(export_path)
    confirmation_index = next(i for i, rec in enumerate(records) if rec["record_type"] == "confirmation")
    external_index = next(i for i, rec in enumerate(records) if rec["record_type"] == "external_action")
    records[confirmation_index], records[external_index] = records[external_index], records[confirmation_index]
    broken_path = tmp_path / "bad_confirmation_order.jsonl"
    _write_jsonl(broken_path, records)
    result = validate_cer_export(str(broken_path))
    assert result["valid"] is False
    assert any("confirmation appears after external action" in v for v in result["violations"])


def test_warrant_assay_record_validates_when_well_formed(tmp_path):
    export_path = run_demo(output_dir=str(tmp_path), approve_confirmation=True)
    records = _read_jsonl(export_path)
    payload = {
        "assay_id": "wa_0001",
        "step_id": "step_001",
        "case_key": "silent_policy_weaken",
        "quadrant": "DANGEROUS",
        "warrant_band": "negative",
        "warranted_action": "REFUSE",
        "alignment": "UNDER_JUSTIFIED",
        "source_receipt_sha256": "a" * 64,
        "record_sha256": "b" * 64,
        "created_at": records[0]["payload"]["started_at"],
    }
    warrant_record = {
        "contract_version": "0.1",
        "schema_version": "0.1",
        "canonical_json_version": records[0]["canonical_json_version"],
        "export_timestamp": records[0]["export_timestamp"],
        "record_type": "warrant_assay",
        "run_id": records[0]["run_id"],
        "provenance_hash": deterministic_hash(payload),
        "signature": sign_payload(payload),
        "signature_algorithm": "hmac-sha256",
        "signing_key_id": records[0]["signing_key_id"],
        "payload": payload,
    }
    records.append(warrant_record)
    path = tmp_path / "with_warrant_assay.jsonl"
    _write_jsonl(path, records)
    result = validate_cer_export(str(path))
    assert result["valid"] is True


def test_warrant_assay_invalid_alignment_fails(tmp_path):
    export_path = run_demo(output_dir=str(tmp_path), approve_confirmation=True)
    records = _read_jsonl(export_path)
    payload = {
        "assay_id": "wa_0001",
        "step_id": "step_001",
        "case_key": "silent_policy_weaken",
        "quadrant": "DANGEROUS",
        "warrant_band": "negative",
        "warranted_action": "REFUSE",
        "alignment": "MAYBE",
        "source_receipt_sha256": "a" * 64,
        "record_sha256": "b" * 64,
        "created_at": records[0]["payload"]["started_at"],
    }
    warrant_record = {
        "contract_version": "0.1",
        "schema_version": "0.1",
        "canonical_json_version": records[0]["canonical_json_version"],
        "export_timestamp": records[0]["export_timestamp"],
        "record_type": "warrant_assay",
        "run_id": records[0]["run_id"],
        "provenance_hash": deterministic_hash(payload),
        "signature": sign_payload(payload),
        "signature_algorithm": "hmac-sha256",
        "signing_key_id": records[0]["signing_key_id"],
        "payload": payload,
    }
    records.append(warrant_record)
    path = tmp_path / "bad_warrant_assay.jsonl"
    _write_jsonl(path, records)
    result = validate_cer_export(str(path))
    assert result["valid"] is False
    assert any("invalid warrant_assay alignment" in v for v in result["violations"])


def test_independent_verifier_records_validate_when_well_formed(tmp_path):
    export_path = run_demo(output_dir=str(tmp_path), approve_confirmation=True)
    records = _read_jsonl(export_path)
    assert any(r["record_type"] == "candidate_find" for r in records)
    assert any(r["record_type"] == "independent_verification" for r in records)
    assert any(r["record_type"] == "verification_result" for r in records)
    result = validate_cer_export(export_path)
    assert result["valid"] is True


def test_verification_result_without_verification_fails(tmp_path):
    export_path = run_demo(output_dir=str(tmp_path), approve_confirmation=True)
    records = [r for r in _read_jsonl(export_path) if r["record_type"] != "independent_verification"]
    path = tmp_path / "missing_verification.jsonl"
    _write_jsonl(path, records)
    result = validate_cer_export(str(path))
    assert result["valid"] is False
    assert any("missing independent_verification" in v for v in result["violations"])
