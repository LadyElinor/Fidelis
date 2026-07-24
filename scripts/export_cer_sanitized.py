from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from pathlib import Path

SENSITIVE_PATTERNS = [
    re.compile(r"authorization", re.IGNORECASE),
    re.compile(r"bearer\s+[a-z0-9\-\._~\+\/=]+", re.IGNORECASE),
    re.compile(r"api[_-]?key", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
]

SAFE_TARGET_HINTS = ("github", "molt", "discord", "slack", "email", "host", "platform")


def scrub_target(target: str) -> str:
    low = (target or "").lower()
    for hint in SAFE_TARGET_HINTS:
        if hint in low:
            return hint
    return "other"


def hash_text(s: str | None) -> str | None:
    if s is None:
        return None
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def export_jsonl(conn: sqlite3.Connection, out_path: Path) -> dict:
    counts = {}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for table in ["runs", "steps", "gate_checks", "confirmations", "gate_check_confirmations", "tool_calls", "external_actions", "receipts", "data_issues", "run_metrics", "drift_signals"]:
            try:
                rows = conn.execute(f"SELECT * FROM {table}").fetchall()
                cols = [d[0] for d in conn.execute(f"SELECT * FROM {table} LIMIT 1").description]
            except sqlite3.Error:
                continue
            counts[table] = len(rows)
            for row in rows:
                rec = dict(zip(cols, row))
                # Redaction rules
                if table == "receipts" and rec.get("receipt_json") is not None:
                    rec["receipt_json_hash"] = hash_text(rec.pop("receipt_json"))
                if table == "external_actions":
                    rec["target"] = scrub_target(str(rec.get("target", "")))
                    rec["payload_hash"] = rec.get("payload_hash") or hash_text(json.dumps(rec, sort_keys=True))
                    rec.pop("auth_evidence", None)
                f.write(json.dumps({"table": table, "record": rec}, ensure_ascii=False) + "\n")
    return counts


def validate_export(out_path: Path) -> list[str]:
    issues: list[str] = []
    for i, line in enumerate(out_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        rec = json.loads(line)
        payload = json.dumps(rec, ensure_ascii=False)
        for pat in SENSITIVE_PATTERNS:
            if pat.search(payload):
                issues.append(f"line {i}: sensitive pattern matched {pat.pattern}")
        table = rec.get("table")
        row = rec.get("record", {})
        if table == "steps" and ("user_text" in row or "assistant_text" in row):
            issues.append(f"line {i}: raw message body found in steps")
        if table == "external_actions" and row.get("target") not in SAFE_TARGET_HINTS and row.get("target") != "other":
            issues.append(f"line {i}: non-sanitized target {row.get('target')}")
    return issues


def main() -> int:
    p = argparse.ArgumentParser(description="Export CER telemetry as sanitized JSONL and validate redaction")
    p.add_argument("--db", default="cer_telemetry.sqlite")
    p.add_argument("--out", default="outputs/cer_export_sanitized.jsonl")
    p.add_argument("--validation-out", default="outputs/cer_export_validation.json")
    args = p.parse_args()

    conn = sqlite3.connect(args.db)
    try:
        counts = export_jsonl(conn, Path(args.out))
    finally:
        conn.close()

    issues = validate_export(Path(args.out))
    validation = {
        "ok": len(issues) == 0,
        "issues": issues,
        "counts": counts,
        "bounds_note": "Metrics in export should be interpreted with lower/upper bound semantics from CER_TELEMETRY_IMPLEMENTATION_v0.1.md",
    }
    Path(args.validation_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.validation_out).write_text(json.dumps(validation, indent=2), encoding="utf-8")
    print(json.dumps({"ok": validation["ok"], "issues": len(issues)}, indent=2))
    return 0 if validation["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
