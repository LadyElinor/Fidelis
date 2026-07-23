from __future__ import annotations

import json
import subprocess
from pathlib import Path

from python_validator.sophron_validate import canonical_json, deterministic_hash, validate_export

REPO_ROOT = Path(__file__).resolve().parents[1]
VECTORS_PATH = REPO_ROOT / "contracts" / "canonical_json_vectors_v0_1.json"
EXPORT_PATH = REPO_ROOT / "node_collector" / "demo_export.jsonl"


def test_python_matches_canonical_vectors():
    vectors = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))
    for vector in vectors:
        assert canonical_json(vector["payload"]) == vector["canonical_json"]
        assert deterministic_hash(vector["payload"]) == vector["sha256"]


def test_node_emits_and_python_validates_bridge():
    subprocess.run(["node", "demoCollector.js"], cwd=REPO_ROOT / "node_collector", check=True)
    result = validate_export(str(EXPORT_PATH))
    assert result["valid"] is True
    assert result["records_processed"] == 3


def test_hash_mismatch_fails(tmp_path):
    subprocess.run(["node", "demoCollector.js"], cwd=REPO_ROOT / "node_collector", check=True)
    records = [json.loads(line) for line in EXPORT_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    records[0]["payload"]["metric_name"] = "tampered_metric"
    broken = tmp_path / "broken.jsonl"
    broken.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
    result = validate_export(str(broken))
    assert result["valid"] is False
    assert any("provenance hash mismatch" in v for v in result["violations"])
