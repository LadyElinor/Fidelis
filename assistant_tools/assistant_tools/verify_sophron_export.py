from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from cer_telemetry.emitter import CerEmitter
from assistant_tools.assistant_tools.verify_mcp_cer_ingest import main as verify_ingest_main


def main() -> int:
    verify_ingest_main()

    repo_root = Path(__file__).resolve().parents[2]
    db_path = repo_root / "outputs" / "mcp_fixture.sqlite"
    export_path = repo_root / "outputs" / "mcp_fixture_for_sophron.jsonl"

    emitter = CerEmitter(str(db_path))
    try:
        run_row = emitter._conn.execute("SELECT run_id FROM runs ORDER BY started_at DESC LIMIT 1").fetchone()
        assert run_row is not None, "Expected at least one run in fixture database"
        run_id = run_row["run_id"]
        emitter.export_for_sophron(run_id=run_id, output_path=str(export_path))
    finally:
        emitter.close()

    records = [json.loads(line) for line in export_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    counts = Counter(record["record_type"] for record in records)

    assert counts["run"] == 1
    assert counts["step"] == 4
    assert counts["gate_check"] == 4
    assert counts["tool_call"] == 4
    assert counts["receipt"] == 4
    assert counts["data_issue"] == 8
    assert counts["confirmation"] == 0
    assert counts["gate_check_confirmation"] == 0
    assert counts["external_action"] == 0

    first = records[0]
    assert first["record_type"] == "run"
    assert first["contract_version"] == "0.1"
    assert first["schema_version"] == "0.1"
    assert first["provenance_hash"].startswith("sha256:")

    print(json.dumps({"ok": True, "export_path": str(export_path), "counts": counts}, indent=2, default=dict))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
