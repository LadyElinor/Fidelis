from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id() -> str:
    return str(uuid.uuid4())


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class CerEmitter:
    db_path: str = "cer_telemetry.sqlite"

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(Path(self.db_path))
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._conn.row_factory = sqlite3.Row

    def close(self) -> None:
        self._conn.close()

    def start_run(self, agent_name: str, channel: str, model: str, config_hash: str, started_at: str | None = None) -> str:
        run_id = _id()
        self._conn.execute(
            """
            INSERT INTO runs(run_id, started_at, ended_at, agent_name, channel, model, config_hash)
            VALUES (?, ?, NULL, ?, ?, ?, ?)
            """,
            (run_id, started_at or _now(), agent_name, channel, model, config_hash),
        )
        self._conn.commit()
        return run_id

    def end_run(self, run_id: str, ended_at: str | None = None) -> None:
        self._conn.execute("UPDATE runs SET ended_at=? WHERE run_id=?", (ended_at or _now(), run_id))
        self._conn.commit()

    def log_step(self, run_id: str, t: int, event_time: str | None = None, user_text_hash: str | None = None, assistant_text_hash: str | None = None) -> str:
        step_id = _id()
        self._conn.execute(
            """
            INSERT INTO steps(step_id, run_id, t, event_time, user_text_hash, assistant_text_hash)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (step_id, run_id, t, event_time or _now(), user_text_hash, assistant_text_hash),
        )
        self._conn.commit()
        return step_id

    def log_gate_check(self, step_id: str, gate: str, decision: str, justification: str, confidence: float | None = None, evidence_ref: str | None = None, created_at: str | None = None) -> str:
        gate_check_id = _id()
        self._conn.execute(
            """
            INSERT INTO gate_checks(gate_check_id, step_id, gate, decision, justification, confidence, evidence_ref, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (gate_check_id, step_id, gate, decision, justification, confidence, evidence_ref, created_at or _now()),
        )
        self._conn.commit()
        return gate_check_id

    def log_confirmation(self, step_id: str, scope: str, confirmed: bool, created_at: str | None = None) -> str:
        confirmation_id = _id()
        self._conn.execute(
            """
            INSERT INTO confirmations(confirmation_id, step_id, scope, confirmed, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (confirmation_id, step_id, scope, int(confirmed), created_at or _now()),
        )
        self._conn.commit()
        return confirmation_id

    def link_gate_check_confirmation(self, gate_check_id: str, confirmation_id: str) -> None:
        self._conn.execute(
            "INSERT INTO gate_check_confirmations(gate_check_id, confirmation_id) VALUES (?, ?)",
            (gate_check_id, confirmation_id),
        )
        self._conn.commit()

    def log_tool_call(self, step_id: str, tool: str, operation: str, args_hash: str, outcome: str, started_at: str, ended_at: str | None = None, error_code: str | None = None) -> str:
        tool_call_id = _id()
        self._conn.execute(
            """
            INSERT INTO tool_calls(tool_call_id, step_id, tool, operation, args_hash, outcome, started_at, ended_at, error_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (tool_call_id, step_id, tool, operation, args_hash, outcome, started_at, ended_at, error_code),
        )
        self._conn.commit()
        return tool_call_id

    def log_external_action(self, step_id: str, type: str, target: str, payload_hash: str, status: str, created_at: str | None = None, failure_reason: str | None = None, auth_evidence: str | None = None) -> str:
        external_action_id = _id()
        self._conn.execute(
            """
            INSERT INTO external_actions(external_action_id, step_id, type, target, payload_hash, status, created_at, failure_reason, auth_evidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (external_action_id, step_id, type, target, payload_hash, status, created_at or _now(), failure_reason, auth_evidence),
        )
        self._conn.commit()
        return external_action_id

    def log_receipt(self, step_id: str, receipt_type: str, fields_present: int, fields_expected: int, receipt_json: str | None = None, created_at: str | None = None) -> str:
        receipt_id = _id()
        self._conn.execute(
            """
            INSERT INTO receipts(receipt_id, step_id, receipt_type, fields_present, fields_expected, receipt_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (receipt_id, step_id, receipt_type, fields_present, fields_expected, receipt_json, created_at or _now()),
        )
        self._conn.commit()
        return receipt_id

    def log_data_issue(self, run_id: str, kind: str, severity: str, details: str, step_id: str | None = None, created_at: str | None = None) -> str:
        issue_id = _id()
        self._conn.execute(
            """
            INSERT INTO data_issues(issue_id, run_id, step_id, kind, severity, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (issue_id, run_id, step_id, kind, severity, details, created_at or _now()),
        )
        self._conn.commit()
        return issue_id

    def _rows_to_dicts(self, query: str, params: tuple = ()) -> list[dict]:
        cur = self._conn.execute(query, params)
        return [dict(row) for row in cur.fetchall()]

    @staticmethod
    def _normalized_json(payload: dict) -> str:
        return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

    def _make_export_record(self, *, record_type: str, run_id: str, export_timestamp: str, payload: dict, schema_version: str = "0.1") -> dict:
        provenance_material = {
            "record_type": record_type,
            "run_id": run_id,
            "schema_version": schema_version,
            "payload": payload,
        }
        provenance_hash = "sha256:" + hashlib.sha256(
            self._normalized_json(provenance_material).encode("utf-8")
        ).hexdigest()
        return {
            "contract_version": "0.1",
            "export_timestamp": export_timestamp,
            "record_type": record_type,
            "schema_version": schema_version,
            "run_id": run_id,
            "provenance_hash": provenance_hash,
            "payload": payload,
            "extensions": {},
        }

    def export_for_sophron(self, run_id: str, output_path: str) -> str:
        export_timestamp = _now()
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        run_rows = self._rows_to_dicts(
            "SELECT run_id, started_at, ended_at, agent_name, channel, model, config_hash FROM runs WHERE run_id = ?",
            (run_id,),
        )
        if not run_rows:
            raise ValueError(f"Run not found: {run_id}")

        steps = self._rows_to_dicts(
            "SELECT step_id, run_id, t, event_time, user_text_hash, assistant_text_hash FROM steps WHERE run_id = ? ORDER BY t, step_id",
            (run_id,),
        )
        step_ids = [row["step_id"] for row in steps]

        def by_steps(query_prefix: str) -> list[dict]:
            if not step_ids:
                return []
            placeholders = ",".join("?" for _ in step_ids)
            return self._rows_to_dicts(query_prefix.format(placeholders=placeholders), tuple(step_ids))

        gate_checks = by_steps(
            "SELECT gate_check_id, step_id, gate, decision, justification, confidence, evidence_ref, created_at FROM gate_checks WHERE step_id IN ({placeholders}) ORDER BY created_at, gate_check_id"
        )
        confirmations = by_steps(
            "SELECT confirmation_id, step_id, scope, confirmed, created_at FROM confirmations WHERE step_id IN ({placeholders}) ORDER BY created_at, confirmation_id"
        )
        tool_calls = by_steps(
            "SELECT tool_call_id, step_id, tool, operation, args_hash, outcome, started_at, ended_at, error_code FROM tool_calls WHERE step_id IN ({placeholders}) ORDER BY started_at, tool_call_id"
        )
        external_actions = by_steps(
            "SELECT external_action_id, step_id, type, target, payload_hash, status, created_at, failure_reason, auth_evidence FROM external_actions WHERE step_id IN ({placeholders}) ORDER BY created_at, external_action_id"
        )
        receipts = by_steps(
            "SELECT receipt_id, step_id, receipt_type, fields_present, fields_expected, receipt_json, created_at FROM receipts WHERE step_id IN ({placeholders}) ORDER BY created_at, receipt_id"
        )

        gate_check_ids = [row["gate_check_id"] for row in gate_checks]
        confirmation_ids = [row["confirmation_id"] for row in confirmations]
        gate_check_confirmations: list[dict] = []
        if gate_check_ids and confirmation_ids:
            gc_placeholders = ",".join("?" for _ in gate_check_ids)
            conf_placeholders = ",".join("?" for _ in confirmation_ids)
            gate_check_confirmations = self._rows_to_dicts(
                f"SELECT gate_check_id, confirmation_id FROM gate_check_confirmations WHERE gate_check_id IN ({gc_placeholders}) AND confirmation_id IN ({conf_placeholders}) ORDER BY gate_check_id, confirmation_id",
                tuple(gate_check_ids + confirmation_ids),
            )

        data_issues = self._rows_to_dicts(
            "SELECT issue_id, run_id, step_id, kind, severity, details, created_at FROM data_issues WHERE run_id = ? ORDER BY created_at, issue_id",
            (run_id,),
        )

        ordered_records: list[tuple[str, dict]] = []
        ordered_records.extend(("run", row) for row in run_rows)
        ordered_records.extend(("step", row) for row in steps)
        ordered_records.extend(("gate_check", row) for row in gate_checks)
        ordered_records.extend(("confirmation", row) for row in confirmations)
        ordered_records.extend(("gate_check_confirmation", row) for row in gate_check_confirmations)
        ordered_records.extend(("tool_call", row) for row in tool_calls)
        ordered_records.extend(("external_action", row) for row in external_actions)
        ordered_records.extend(("receipt", row) for row in receipts)
        ordered_records.extend(("data_issue", row) for row in data_issues)

        with out_path.open("w", encoding="utf-8") as fh:
            for record_type, payload in ordered_records:
                fh.write(self._normalized_json(self._make_export_record(
                    record_type=record_type,
                    run_id=run_id,
                    export_timestamp=export_timestamp,
                    payload=payload,
                )))
                fh.write("\n")

        return str(out_path)
