from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cer_telemetry.emitter import CerEmitter, hash_text


SAFE_PATTERN_NAMES = (
    "email-like-content",
    "key-like-content",
    "ssn-like-content",
    "card-like-content",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_json(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


@dataclass
class MCPLeakPolicy:
    minimum_indicator_count: int = 2
    redaction_mismatch_score: float = 0.7
    enabled_patterns: dict[str, bool] = field(
        default_factory=lambda: {name: True for name in SAFE_PATTERN_NAMES}
    )

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "MCPLeakPolicy":
        payload = payload or {}
        enabled = {name: True for name in SAFE_PATTERN_NAMES}
        for name, cfg in (payload.get("patterns") or {}).items():
            if isinstance(cfg, dict) and "enabled" in cfg:
                enabled[name] = bool(cfg["enabled"])
        return cls(
            minimum_indicator_count=int(payload.get("minimumIndicatorCount", 2)),
            redaction_mismatch_score=float(payload.get("redactionMismatchScore", 0.7)),
            enabled_patterns=enabled,
        )


def extract_leak_indicators(details: Any, policy: MCPLeakPolicy) -> list[str]:
    if details is None:
        return []
    text = json.dumps(details, ensure_ascii=False, sort_keys=True) if not isinstance(details, str) else details
    lowered = text.lower()
    indicators: list[str] = []

    if policy.enabled_patterns.get("email-like-content", True) and "@" in text:
        indicators.append("email-like-content")
    if policy.enabled_patterns.get("ssn-like-content", True) and any(token in text for token in ["123-45-6789", "ssn"]):
        indicators.append("ssn-like-content")
    if policy.enabled_patterns.get("card-like-content", True) and any(token in text for token in ["4111", "4242", "card"]):
        indicators.append("card-like-content")
    if policy.enabled_patterns.get("key-like-content", True) and any(token in lowered for token in ["sk-live-", "api_key", "secret", "token"]):
        indicators.append("key-like-content")

    return indicators


@dataclass
class MCPCerIngestSession:
    db_path: str = "cer_telemetry.sqlite"
    agent_name: str = "mcp-runtime"
    channel: str = "mcp"
    model: str = "unknown"
    config_hash: str = "unknown"
    leak_policy: MCPLeakPolicy = field(default_factory=MCPLeakPolicy)

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

    def ingest_event(self, event: dict[str, Any]) -> str:
        step_id = self._emitter.log_step(
            run_id=self.run_id,
            t=self._t,
            event_time=str(event.get("timestamp") or _now_iso()),
            user_text_hash=hash_text(json.dumps(event.get("input"), sort_keys=True, ensure_ascii=False)) if event.get("input") is not None else None,
            assistant_text_hash=hash_text(json.dumps(event.get("output"), sort_keys=True, ensure_ascii=False)) if event.get("output") is not None else None,
        )
        self._t += 1

        tool_name = str(event.get("tool") or event.get("event_type") or "unknown")
        operation = str(event.get("operation") or event.get("kind") or "event")
        outcome = str(event.get("outcome") or "success").lower()
        ok = outcome not in {"fail", "failed", "error"}
        started_at = str(event.get("started_at") or event.get("timestamp") or _now_iso())
        ended_at = str(event.get("ended_at") or event.get("timestamp") or _now_iso())
        error_code = None if ok else str(event.get("error_code") or "mcp_event_failed")

        self._emitter.log_tool_call(
            step_id=step_id,
            tool=tool_name,
            operation=operation,
            args_hash=_sha256_json(event.get("input") or event),
            outcome="success" if ok else "fail",
            started_at=started_at,
            ended_at=ended_at,
            error_code=error_code,
        )

        gate = str(event.get("gate") or "traceability")
        decision = str(event.get("decision") or ("pass" if ok else "warn"))
        if gate in {"intent", "authority", "irreversibility", "exposure", "traceability"} and decision in {"pass", "warn", "escalate", "block"}:
            self._emitter.log_gate_check(
                step_id=step_id,
                gate=gate,
                decision=decision,
                justification=str(event.get("justification") or f"MCP event {tool_name}/{operation}"),
                confidence=event.get("confidence"),
                evidence_ref=str(event.get("event_id") or event.get("trace_id") or "") or None,
                created_at=_now_iso(),
            )

        external_action = event.get("external_action")
        if isinstance(external_action, dict):
            action_type = str(external_action.get("type") or "other")
            if action_type not in {"post", "reply", "dm", "email", "purchase", "delete", "upload", "other"}:
                action_type = "other"
            status = str(external_action.get("status") or "attempted")
            if status not in {"attempted", "blocked", "sent", "failed"}:
                status = "attempted"
            self._emitter.log_external_action(
                step_id=step_id,
                type=action_type,
                target=str(external_action.get("target") or "unknown"),
                payload_hash=_sha256_json(external_action.get("payload") or external_action),
                status=status,
                created_at=_now_iso(),
                failure_reason=external_action.get("failure_reason"),
                auth_evidence=external_action.get("auth_evidence"),
            )

        receipt_payload = {
            "event_id": event.get("event_id"),
            "session_id": event.get("session_id"),
            "trace_id": event.get("trace_id"),
            "tool": event.get("tool"),
            "operation": event.get("operation"),
            "outcome": outcome,
            "risk_flags": event.get("risk_flags") or [],
        }
        if not event.get("session_id") or not event.get("trace_id"):
            self._emitter.log_data_issue(
                run_id=self.run_id,
                step_id=step_id,
                kind="missing_row",
                severity="warn",
                details="missing session_id or trace_id",
                created_at=_now_iso(),
            )
        fields_expected = 7
        fields_present = sum(1 for value in receipt_payload.values() if value not in (None, [], ""))
        self._emitter.log_receipt(
            step_id=step_id,
            receipt_type="action",
            fields_present=fields_present,
            fields_expected=fields_expected,
            receipt_json=json.dumps(receipt_payload, sort_keys=True, ensure_ascii=False),
            created_at=_now_iso(),
        )

        risk_flags = list(event.get("risk_flags") or [])
        details = event.get("details")
        indicators = extract_leak_indicators(details, self.leak_policy)
        if len(indicators) >= self.leak_policy.minimum_indicator_count:
            risk_flags.extend(indicators)

        redaction_claimed = bool(event.get("redacted") or event.get("claims_redacted"))
        if redaction_claimed and indicators and float(event.get("redaction_score") or 1.0) >= self.leak_policy.redaction_mismatch_score:
            risk_flags.append("redaction-claim-content-mismatch")

        if event.get("session_mismatch"):
            risk_flags.append("scope-escalation")
        if event.get("orphan_trace"):
            risk_flags.append("orphan-trace")
        if event.get("redaction_unknown"):
            risk_flags.append("unknown-redaction-status")

        if not ok:
            self._emitter.log_data_issue(
                run_id=self.run_id,
                step_id=step_id,
                kind="other",
                severity="warn",
                details=f"MCP event failed: {tool_name}/{operation}",
                created_at=_now_iso(),
            )

        for flag in sorted(set(risk_flags)):
            kind = "redaction_gap" if "redaction" in flag or flag in SAFE_PATTERN_NAMES else "other"
            severity = "warn" if flag not in {"scope-escalation", "orphan-trace"} else "error"
            self._emitter.log_data_issue(
                run_id=self.run_id,
                step_id=step_id,
                kind=kind,
                severity=severity,
                details=flag,
                created_at=_now_iso(),
            )

        return step_id


def ingest_mcp_events_jsonl(
    input_path: str,
    db_path: str = "cer_telemetry.sqlite",
    agent_name: str = "mcp-runtime",
    channel: str = "mcp",
    model: str = "unknown",
    config_hash: str | None = None,
    leak_policy: dict[str, Any] | None = None,
) -> str:
    source = Path(input_path)
    if config_hash is None:
        config_hash = hashlib.sha256(str(source).encode("utf-8")).hexdigest()

    session = MCPCerIngestSession(
        db_path=db_path,
        agent_name=agent_name,
        channel=channel,
        model=model,
        config_hash=config_hash,
        leak_policy=MCPLeakPolicy.from_dict(leak_policy),
    )
    try:
        for line in source.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            session.ingest_event(json.loads(line))
        return session.run_id
    finally:
        session.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest MCP event JSONL into CER telemetry SQLite")
    parser.add_argument("input", help="Path to MCP JSONL events")
    parser.add_argument("--db", default="cer_telemetry.sqlite")
    parser.add_argument("--agent-name", default="mcp-runtime")
    parser.add_argument("--channel", default="mcp")
    parser.add_argument("--model", default="unknown")
    parser.add_argument("--config-hash", default=None)
    parser.add_argument("--leak-policy", default=None, help="Optional JSON file containing leak policy overrides")
    args = parser.parse_args()

    leak_policy = None
    if args.leak_policy:
        leak_policy = json.loads(Path(args.leak_policy).read_text(encoding="utf-8"))

    run_id = ingest_mcp_events_jsonl(
        input_path=args.input,
        db_path=args.db,
        agent_name=args.agent_name,
        channel=args.channel,
        model=args.model,
        config_hash=args.config_hash,
        leak_policy=leak_policy,
    )
    print(json.dumps({"ok": True, "run_id": run_id}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
