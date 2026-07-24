from __future__ import annotations

import argparse
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        Path("cer_telemetry/migrations/0002_run_metrics.sql").read_text(encoding="utf-8")
    )


def backfill_run_metrics(conn: sqlite3.Connection) -> None:
    sql = """
    INSERT OR REPLACE INTO run_metrics(
      run_id, step_count, gate_check_count, safety_exception_rate,
      exposure_attempt_rate, receipt_completeness, confirmation_violation_count, created_at
    )
    WITH
    step_counts AS (
      SELECT run_id, COUNT(*) AS step_count
      FROM steps GROUP BY run_id
    ),
    gate_counts AS (
      SELECT s.run_id,
             COUNT(*) AS gate_count,
             SUM(CASE WHEN gc.decision IN ('warn','escalate','block') THEN 1 ELSE 0 END) AS exception_count
      FROM gate_checks gc
      JOIN steps s ON s.step_id = gc.step_id
      GROUP BY s.run_id
    ),
    exposure_counts AS (
      SELECT s.run_id,
             SUM(CASE WHEN ea.status IN ('attempted','sent','blocked') THEN 1 ELSE 0 END) AS exposure_events
      FROM external_actions ea
      JOIN steps s ON s.step_id = ea.step_id
      GROUP BY s.run_id
    ),
    receipt_stats AS (
      SELECT s.run_id,
             AVG(CASE WHEN r.fields_expected > 0 THEN 1.0 * r.fields_present / r.fields_expected END) AS receipt_completeness
      FROM receipts r
      JOIN steps s ON s.step_id = r.step_id
      GROUP BY s.run_id
    ),
    confirmation_violations AS (
      SELECT s.run_id,
             SUM(CASE WHEN ea.status = 'sent' AND c.confirmation_id IS NULL THEN 1 ELSE 0 END) AS vio_count
      FROM external_actions ea
      JOIN steps s ON s.step_id = ea.step_id
      LEFT JOIN confirmations c
        ON c.step_id = ea.step_id
       AND c.scope IN ('external_action','message_send','deletion','purchase','credential_change')
       AND c.confirmed = 1
      GROUP BY s.run_id
    )
    SELECT
      r.run_id,
      COALESCE(sc.step_count, 0) AS step_count,
      COALESCE(gc.gate_count, 0) AS gate_check_count,
      CASE WHEN COALESCE(gc.gate_count,0)=0 THEN NULL ELSE 1.0 * COALESCE(gc.exception_count,0)/gc.gate_count END AS safety_exception_rate,
      CASE WHEN COALESCE(sc.step_count,0)=0 THEN NULL ELSE 1.0 * COALESCE(ec.exposure_events,0)/sc.step_count END AS exposure_attempt_rate,
      rs.receipt_completeness,
      COALESCE(cv.vio_count, 0) AS confirmation_violation_count,
      ? AS created_at
    FROM runs r
    LEFT JOIN step_counts sc ON sc.run_id = r.run_id
    LEFT JOIN gate_counts gc ON gc.run_id = r.run_id
    LEFT JOIN exposure_counts ec ON ec.run_id = r.run_id
    LEFT JOIN receipt_stats rs ON rs.run_id = r.run_id
    LEFT JOIN confirmation_violations cv ON cv.run_id = r.run_id
    """
    conn.execute(sql, (now_iso(),))


def compute_signals(conn: sqlite3.Connection, alpha: float, out_json: Path) -> dict:
    rows = conn.execute(
        """
        SELECT rm.run_id, r.started_at, r.config_hash,
               rm.safety_exception_rate, rm.exposure_attempt_rate, rm.receipt_completeness,
               rm.confirmation_violation_count
        FROM run_metrics rm
        JOIN runs r ON r.run_id = rm.run_id
        ORDER BY r.started_at
        """
    ).fetchall()

    ewm = {
        "safety_exception_rate": None,
        "exposure_attempt_rate": None,
        "receipt_completeness": None,
    }
    cusum = 0.0
    baseline_violation_rate = 0.05
    alert_threshold = 3.0
    signals = []

    conn.execute("DELETE FROM drift_signals")

    for run_id, _started, config_hash, safety, exposure, receipt, vio_count in rows:
        metrics = {
            "safety_exception_rate": safety,
            "exposure_attempt_rate": exposure,
            "receipt_completeness": receipt,
        }
        for metric, value in metrics.items():
            if value is None:
                continue
            if ewm[metric] is None:
                ewm[metric] = value
            else:
                ewm[metric] = alpha * value + (1 - alpha) * ewm[metric]
            sig = {
                "signal_id": str(uuid.uuid4()),
                "run_id": run_id,
                "metric": metric,
                "ewma_value": ewm[metric],
                "cusum_value": None,
                "alert": 0,
                "details": json.dumps({"config_hash": config_hash}),
                "created_at": now_iso(),
            }
            signals.append(sig)

        vio = float(vio_count or 0)
        cusum = max(0.0, cusum + (vio - baseline_violation_rate))
        cusum_alert = 1 if cusum >= alert_threshold else 0
        signals.append(
            {
                "signal_id": str(uuid.uuid4()),
                "run_id": run_id,
                "metric": "confirmation_violation_cusum",
                "ewma_value": None,
                "cusum_value": cusum,
                "alert": cusum_alert,
                "details": json.dumps({"violation_count": vio_count, "baseline": baseline_violation_rate}),
                "created_at": now_iso(),
            }
        )

    conn.executemany(
        """
        INSERT INTO drift_signals(signal_id, run_id, metric, ewma_value, cusum_value, alert, details, created_at)
        VALUES (:signal_id, :run_id, :metric, :ewma_value, :cusum_value, :alert, :details, :created_at)
        """,
        signals,
    )

    config_rows = conn.execute(
        """
        SELECT r.config_hash,
               COUNT(*) AS runs,
               AVG(rm.safety_exception_rate) AS avg_safety_exception_rate,
               AVG(rm.exposure_attempt_rate) AS avg_exposure_attempt_rate,
               AVG(rm.receipt_completeness) AS avg_receipt_completeness
        FROM run_metrics rm
        JOIN runs r ON r.run_id = rm.run_id
        GROUP BY r.config_hash
        ORDER BY runs DESC
        """
    ).fetchall()

    report = {
        "alpha": alpha,
        "run_count": len(rows),
        "signals_written": len(signals),
        "config_diff_summary": [
            {
                "config_hash": r[0],
                "runs": r[1],
                "avg_safety_exception_rate": r[2],
                "avg_exposure_attempt_rate": r[3],
                "avg_receipt_completeness": r[4],
            }
            for r in config_rows
        ],
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    p = argparse.ArgumentParser(description="CER drift monitor: run_metrics + EWMA/CUSUM + config diffs")
    p.add_argument("--db", default="cer_telemetry.sqlite")
    p.add_argument("--alpha", type=float, default=0.3)
    p.add_argument("--out", default="outputs/cer_drift_report.json")
    args = p.parse_args()

    conn = sqlite3.connect(args.db)
    try:
        ensure_tables(conn)
        backfill_run_metrics(conn)
        report = compute_signals(conn, alpha=args.alpha, out_json=Path(args.out))
        conn.commit()
    finally:
        conn.close()

    print(json.dumps({"ok": True, "run_count": report["run_count"], "signals": report["signals_written"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
