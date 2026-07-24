from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

QUERY_ORDER = [
    "gate_decision_rates.sql",
    "safety_exception_rate_per_100_steps.sql",
    "exposure_attempt_send_block_rates.sql",
    "confirmation_compliance_violations_bounds.sql",
    "confirmation_latency_by_scope.sql",
    "receipt_completeness.sql",
    "data_issues_summary.sql",
]


def run_query(conn: sqlite3.Connection, sql_path: Path) -> list[tuple]:
    sql = sql_path.read_text(encoding="utf-8")
    cur = conn.execute(sql)
    cols = [d[0] for d in cur.description] if cur.description else []
    rows = cur.fetchall()
    return [tuple(cols)] + rows


def format_table(rows: list[tuple]) -> str:
    if not rows:
        return "(no rows)"
    widths = [max(len(str(row[i])) for row in rows) for i in range(len(rows[0]))]
    out = []
    for idx, row in enumerate(rows):
        out.append(" | ".join(str(row[i]).ljust(widths[i]) for i in range(len(row))))
        if idx == 0:
            out.append("-+-".join("-" * widths[i] for i in range(len(row))))
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CER Safety CI SQL query pack")
    parser.add_argument("--db", default="cer_telemetry.sqlite")
    parser.add_argument("--queries", default="queries")
    parser.add_argument("--out", default="outputs/cer_safety_ci_report.txt")
    args = parser.parse_args()

    db_path = Path(args.db)
    qdir = Path(args.queries)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        sections = []
        for name in QUERY_ORDER:
            qpath = qdir / name
            rows = run_query(conn, qpath)
            sections.append(f"## {name}\n\n{format_table(rows)}\n")

        report = "# CER Safety CI Report\n\n" + "\n".join(sections)
        out_path.write_text(report, encoding="utf-8")
        print(f"ok: wrote {out_path}")
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
