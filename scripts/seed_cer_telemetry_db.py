from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def apply_sql_file(conn: sqlite3.Connection, path: Path) -> None:
    conn.executescript(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an empty CER telemetry SQLite DB")
    parser.add_argument("--db", default="cer_telemetry.sqlite", help="Output sqlite file path")
    parser.add_argument("--schema", default="cer_telemetry/schema.sql")
    parser.add_argument("--indexes", default="cer_telemetry/indexes.sql")
    args = parser.parse_args()

    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        apply_sql_file(conn, Path(args.schema))
        apply_sql_file(conn, Path(args.indexes))
        conn.commit()
    finally:
        conn.close()

    print(f"ok: created {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
