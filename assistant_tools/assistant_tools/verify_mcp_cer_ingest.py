from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from assistant_tools.assistant_tools.cer_openclaw_integration import _now_iso
from assistant_tools.assistant_tools.mcp_cer_ingest import ingest_mcp_events_jsonl


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    db_path = repo_root / "outputs" / "mcp_fixture.sqlite"
    fixture_path = repo_root / "assistant_tools" / "assistant_tools" / "mcp_mixed_session_fixture.jsonl"
    leak_policy = repo_root / "assistant_tools" / "assistant_tools" / "mcp_leak_policy_fixture.json"

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    schema_path = repo_root / "cer_telemetry" / "schema.sql"
    indexes_path = repo_root / "cer_telemetry" / "indexes.sql"
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(schema_path.read_text(encoding="utf-8"))
        conn.executescript(indexes_path.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()

    policy = json.loads(leak_policy.read_text(encoding="utf-8"))
    run_id = ingest_mcp_events_jsonl(
        input_path=str(fixture_path),
        db_path=str(db_path),
        agent_name="mcp-runtime",
        channel="mcp",
        model="mcp-fixture",
        config_hash="cfg-mcp-fixture-0001",
        leak_policy=policy,
    )

    conn = sqlite3.connect(db_path)
    try:
        counts = {}
        for table in ["runs", "steps", "tool_calls", "gate_checks", "receipts", "data_issues"]:
            counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        risk_flags = [row[0] for row in conn.execute("SELECT details FROM data_issues ORDER BY details")]
    finally:
        conn.close()

    assert counts["runs"] == 1
    assert counts["steps"] == 4
    assert counts["tool_calls"] == 4
    assert counts["receipts"] == 4
    assert counts["data_issues"] >= 5
    assert "scope-escalation" in risk_flags
    assert "orphan-trace" in risk_flags
    assert "unknown-redaction-status" in risk_flags
    assert "redaction-claim-content-mismatch" in risk_flags
    assert "email-like-content" in risk_flags
    assert "ssn-like-content" in risk_flags
    assert "key-like-content" in risk_flags

    print(json.dumps({"ok": True, "run_id": run_id, "counts": counts, "checked_at": _now_iso()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
