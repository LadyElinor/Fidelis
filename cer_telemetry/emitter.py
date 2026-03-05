from __future__ import annotations

import hashlib
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
