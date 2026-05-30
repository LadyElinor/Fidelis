"""CER emitter for the runnable minimal proof.

This is in-memory by design, but it enforces contract-relevant behavior:
- deterministic provenance hashes
- structured record types
- escalation branches
- confirmation logging
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from .hash_utils import CANONICAL_JSON_VERSION, deterministic_hash
except ImportError:  # pragma: no cover
    from hash_utils import CANONICAL_JSON_VERSION, deterministic_hash


VALID_GATES = {
    "manifest_integrity",
    "least_privilege",
    "consent_traceability",
    "token_handling",
    "output_sanitization",
    "tool_poisoning",
    "session_isolation",
    "scope_creep",
    "provenance_verification",
    "irreversibility",
}
VALID_DECISIONS = {"pass", "warn", "escalate", "block"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ConfirmationProvider:
    """Simulated human/operator approval provider."""

    approve: bool = True

    def request(self, *, step_id: str, scope: str, reason: str) -> bool:
        print(f"[Confirmation Required] {scope} | step={step_id} | reason={reason}")
        print(f"[Confirmation] {'CONFIRMED' if self.approve else 'REJECTED'}")
        return self.approve


class CerEmitter:
    def __init__(self, confirmation_provider: Optional[ConfirmationProvider] = None):
        self.records: List[Dict[str, Any]] = []
        self.run_id = f"run_{int(time.time())}"
        self.confirmation_provider = confirmation_provider or ConfirmationProvider(True)

    def _append(self, record_type: str, payload: Dict[str, Any]) -> None:
        self.records.append({"record_type": record_type, "payload": payload})

    def start_run(self, agent_name: str = "demo_agent") -> str:
        payload = {
            "run_id": self.run_id,
            "started_at": utc_now(),
            "agent_name": agent_name,
            "channel": "mcp_demo",
        }
        self._append("run", payload)
        print(f"[CER] Started run: {self.run_id}")
        return self.run_id

    def log_hazard_map(self, hazard_payload: Dict[str, Any]) -> None:
        self._append("hazard_map", hazard_payload)
        print(f"[EthicsCouncil] Risk Level: {hazard_payload.get('overall_risk', 'unknown').upper()}")

    def log_mcp_gate_check(
        self,
        *,
        step_id: str,
        gate: str,
        decision: str,
        justification: str,
        confidence: float = 0.85,
        evidence_ref: Optional[str] = None,
    ) -> str:
        if gate not in VALID_GATES:
            raise ValueError(f"Invalid MCP gate: {gate}")
        if decision not in VALID_DECISIONS:
            raise ValueError(f"Invalid decision: {decision}")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

        gate_check_id = f"gc_{len(self.records)+1:04d}"
        payload = {
            "gate_check_id": gate_check_id,
            "step_id": step_id,
            "gate": gate,
            "decision": decision,
            "justification": justification,
            "confidence": confidence,
            "evidence_ref": evidence_ref,
            "created_at": utc_now(),
        }
        self._append("gate_check", payload)
        print(f"[CER Gate] {gate:22} -> {decision:8} | {justification}")
        return gate_check_id

    def request_confirmation(self, *, step_id: str, scope: str, reason: str) -> bool:
        confirmed = self.confirmation_provider.request(step_id=step_id, scope=scope, reason=reason)
        self._append(
            "confirmation",
            {
                "confirmation_id": f"conf_{len(self.records)+1:04d}",
                "step_id": step_id,
                "scope": scope,
                "reason": reason,
                "confirmed": confirmed,
                "created_at": utc_now(),
            },
        )
        return confirmed

    def log_external_action(self, *, step_id: str, action: str, target: str, status: str) -> None:
        self._append(
            "external_action",
            {
                "external_action_id": f"act_{len(self.records)+1:04d}",
                "step_id": step_id,
                "action": action,
                "target": target,
                "status": status,
                "created_at": utc_now(),
            },
        )

    def export_for_sophron(self, output_path: Optional[str] = None) -> str:
        if output_path is None:
            output_path = f"demo_export_{self.run_id}.jsonl"
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as f:
            for record in self.records:
                payload = record["payload"]
                envelope = {
                    "contract_version": "0.1",
                    "schema_version": "0.1",
                    "canonical_json_version": CANONICAL_JSON_VERSION,
                    "export_timestamp": utc_now(),
                    "record_type": record["record_type"],
                    "run_id": self.run_id,
                    "provenance_hash": deterministic_hash(payload),
                    "payload": payload,
                }
                f.write(json.dumps(envelope, sort_keys=True, ensure_ascii=False) + "\n")

        print(f"[CER] Exported {len(self.records)} records -> {path}")
        return str(path)
