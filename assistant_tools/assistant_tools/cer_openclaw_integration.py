from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from cer_telemetry.emitter import CerEmitter, hash_text
except ModuleNotFoundError:
    import sys
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from cer_telemetry.emitter import CerEmitter, hash_text


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_json(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


@dataclass
class OpenClawCerSession:
    """Thin wiring layer from OpenClaw-style workflow events to CER telemetry."""

    db_path: str = "cer_telemetry.sqlite"
    agent_name: str = "openclaw-assistant"
    channel: str = "cli"
    model: str = "unknown"
    config_hash: str = "unknown"

    def __post_init__(self) -> None:
        self._emitter = CerEmitter(self.db_path)
        self.run_id = self._emitter.start_run(
            agent_name=self.agent_name,
            channel=self.channel,
            model=self.model,
            config_hash=self.config_hash,
            started_at=_now_iso(),
        )
        self._t = 0

    def close(self) -> None:
        self._emitter.end_run(self.run_id, ended_at=_now_iso())
        self._emitter.close()

    def log_exchange(self, user_text: str | None, assistant_text: str | None, event_time: str | None = None) -> str:
        step_id = self._emitter.log_step(
            run_id=self.run_id,
            t=self._t,
            event_time=event_time or _now_iso(),
            user_text_hash=hash_text(user_text) if user_text else None,
            assistant_text_hash=hash_text(assistant_text) if assistant_text else None,
        )
        self._t += 1
        return step_id

    def log_tool_call(
        self,
        step_id: str,
        tool: str,
        operation: str,
        args_payload: Any,
        ok: bool,
        started_at: str,
        ended_at: str | None = None,
        error_code: str | None = None,
    ) -> str:
        return self._emitter.log_tool_call(
            step_id=step_id,
            tool=tool,
            operation=operation,
            args_hash=_sha256_json(args_payload),
            outcome="success" if ok else "fail",
            started_at=started_at,
            ended_at=ended_at,
            error_code=error_code,
        )

    def log_gate(self, step_id: str, gate: str, decision: str, justification: str, confidence: float | None = None) -> str:
        return self._emitter.log_gate_check(
            step_id=step_id,
            gate=gate,
            decision=decision,
            justification=justification,
            confidence=confidence,
            evidence_ref=None,
            created_at=_now_iso(),
        )

    def log_confirmation(self, step_id: str, scope: str, confirmed: bool) -> str:
        return self._emitter.log_confirmation(step_id=step_id, scope=scope, confirmed=confirmed, created_at=_now_iso())

    def log_external_action(self, step_id: str, action_type: str, target: str, payload: Any, status: str, failure_reason: str | None = None) -> str:
        return self._emitter.log_external_action(
            step_id=step_id,
            type=action_type,
            target=target,
            payload_hash=_sha256_json(payload),
            status=status,
            created_at=_now_iso(),
            failure_reason=failure_reason,
            auth_evidence=None,
        )

    def log_receipt(self, step_id: str, receipt_type: str, fields_present: int, fields_expected: int, receipt_payload: Any | None = None) -> str:
        receipt_json = json.dumps(receipt_payload, ensure_ascii=False, sort_keys=True) if receipt_payload is not None else None
        return self._emitter.log_receipt(
            step_id=step_id,
            receipt_type=receipt_type,
            fields_present=fields_present,
            fields_expected=fields_expected,
            receipt_json=receipt_json,
            created_at=_now_iso(),
        )

    def log_data_issue(self, kind: str, severity: str, details: str, step_id: str | None = None) -> str:
        return self._emitter.log_data_issue(
            run_id=self.run_id,
            step_id=step_id,
            kind=kind,
            severity=severity,
            details=details,
            created_at=_now_iso(),
        )


def ingest_workflow_summary_to_cer(summary_path: str, db_path: str = "cer_telemetry.sqlite", model: str = "workflow-smoke") -> str:
    summary = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    cfg_hash = hashlib.sha256((summary.get("repo_url") or "").encode("utf-8")).hexdigest()
    session = OpenClawCerSession(db_path=db_path, model=model, config_hash=cfg_hash)
    try:
        steps = summary.get("steps", [])
        for s in steps:
            user_text = f"execute step: {s.get('name')}"
            assistant_text = json.dumps(s, ensure_ascii=False, sort_keys=True)
            step_id = session.log_exchange(user_text=user_text, assistant_text=assistant_text)

            ts = _now_iso()
            session.log_tool_call(
                step_id=step_id,
                tool=s.get("name", "unknown"),
                operation="workflow_step",
                args_payload=s,
                ok=bool(s.get("ok", False)),
                started_at=ts,
                ended_at=_now_iso(),
                error_code=None if s.get("ok", False) else "step_failed",
            )

            if s.get("name") == "safety_gate":
                decision = "pass" if s.get("ok") else "block"
                gc = session.log_gate(step_id=step_id, gate="traceability", decision=decision, justification="safety_gate summary")
                # For gating around external actions, require explicit confirmation.
                conf = session.log_confirmation(step_id=step_id, scope="external_action", confirmed=bool(s.get("ok")))
                session._emitter.link_gate_check_confirmation(gc, conf)

            if s.get("name") == "repo_ingest":
                status = "sent" if s.get("ok") else "failed"
                session.log_external_action(
                    step_id=step_id,
                    action_type="other",
                    target="github",
                    payload={"repo_url": summary.get("repo_url")},
                    status=status,
                    failure_reason=None if s.get("ok") else "repo_ingest_failed",
                )

            if s.get("name") == "receipt":
                session.log_receipt(
                    step_id=step_id,
                    receipt_type="action",
                    fields_present=2,
                    fields_expected=2,
                    receipt_payload={"path": s.get("path")},
                )

            if not s.get("ok", False):
                session.log_data_issue(kind="other", severity="warn", details=f"workflow step failed: {s.get('name')}", step_id=step_id)

        # emit data issue if no explicit confirmation-bearing step found
        saw_confirmation_candidate = any(st.get("name") == "safety_gate" for st in steps)
        if not saw_confirmation_candidate:
            session.log_data_issue(
                kind="missing_confirmation",
                severity="warn",
                details="No safety_gate step available to derive explicit confirmation linkage",
            )

        return session.run_id
    finally:
        session.close()
