#!/usr/bin/env python3
"""Minimal VITA-M1.1 reference interpreter for TrustworthyAgentStack.

This module is intentionally small and explicit. It models the core VITA-M1.1
loop in a way that is easy to inspect and test:

OBSERVE -> BIND -> TEST -> ACT -> RECEIPT -> REVIEW
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


CLAIM_STRENGTH_LIMITS = {
    "OBSERVED": "BEHAVIORAL_FACT",
    "MEASURED": "BEHAVIORAL_FACT",
    "REPORTED": "SOURCE_BOUND",
    "INFERRED": "PROBABLE",
    "SIMULATED": "HYPOTHETICAL",
    "DERIVED": "DERIVED_FACT",
    "HUMAN_REVIEWED": "REVIEWED_JUDGMENT",
}

ALLOWED_AFTER_CORRECTIVE_HALT = {
    "REPORT",
    "REVIEW",
    "EXPORT_RECEIPTS",
    "REQUEST_HUMAN_REVIEW",
    "PATCH",
    "SHUTDOWN",
}


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonicalize(text: str) -> str:
    return " ".join(text.strip().split())


@dataclass
class EvidenceItem:
    id: str
    type: str
    claim: str
    source: str
    hash: str


@dataclass
class Receipt:
    receipt_id: str
    op: str
    input_hash: str
    context_hash: str
    evidence: List[Dict[str, Any]]
    claim_strength: str
    risk_state: str
    decision: str
    plurality_result: str
    reviewable: bool
    review_of: Optional[str]
    limitations: List[str]
    prev_receipt: str
    timestamp: float
    receipt_hash: str = ""

    def seal(self) -> "Receipt":
        payload = {
            "receipt_id": self.receipt_id,
            "op": self.op,
            "input_hash": self.input_hash,
            "context_hash": self.context_hash,
            "evidence": self.evidence,
            "claim_strength": self.claim_strength,
            "risk_state": self.risk_state,
            "decision": self.decision,
            "plurality_result": self.plurality_result,
            "reviewable": self.reviewable,
            "review_of": self.review_of,
            "limitations": self.limitations,
            "prev_receipt": self.prev_receipt,
            "timestamp": self.timestamp,
        }
        self.receipt_hash = sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        return self


@dataclass
class VitaState:
    mission: str
    context: str = ""
    previous_receipt_hash: str = "GENESIS"
    counter: int = 0
    receipts: List[Receipt] = field(default_factory=list)
    corrective_halt: bool = False
    halt_reason: Optional[str] = None


class VitaM11:
    def __init__(self, mission: str, context: str = ""):
        self.state = VitaState(mission=mission, context=context)

    def parse_intent(self, text: str) -> Dict[str, Any]:
        lowered = text.lower()
        requests_harm = any(
            phrase in lowered
            for phrase in [
                "harm someone",
                "kill",
                "make a weapon",
                "poison",
                "exploit",
                "destroy evidence",
                "deceive them",
            ]
        )
        requests_creation = any(phrase in lowered for phrase in ["create", "write", "design", "build", "draft"])
        requests_review = any(phrase in lowered for phrase in ["review", "reassess", "reconsider", "revise"])
        irreversible = any(phrase in lowered for phrase in ["permanently", "irreversibly", "cannot be undone", "final only"])
        forces_single_value = any(phrase in lowered for phrase in ["only acceptable value", "single value system", "everyone must adopt"])
        blocks_appeal = any(phrase in lowered for phrase in ["no appeals", "prevent appeals", "no correction"])
        dehumanizes = any(phrase in lowered for phrase in ["low-value humans", "dispose of people", "human cattle"])
        mentions_life = any(phrase in lowered for phrase in ["life", "flourish", "preserve", "alignment", "dignity", "plurality"])
        return {
            "raw": text,
            "requests_harm": requests_harm,
            "requests_creation": requests_creation,
            "requests_review": requests_review,
            "irreversible": irreversible,
            "forces_single_value": forces_single_value,
            "blocks_appeal": blocks_appeal,
            "dehumanizes": dehumanizes,
            "mentions_life": mentions_life,
        }

    def collect_evidence(self, text: str, evidence_type: str = "OBSERVED") -> List[EvidenceItem]:
        if evidence_type not in CLAIM_STRENGTH_LIMITS:
            raise ValueError(f"Unsupported evidence type: {evidence_type}")
        return [
            EvidenceItem(
                id="ev_000001",
                type=evidence_type,
                claim=text,
                source="user_input",
                hash=sha256_text(text),
            )
        ]

    def claim_strength_for(self, evidence: List[EvidenceItem]) -> str:
        strengths = {CLAIM_STRENGTH_LIMITS[item.type] for item in evidence}
        if "HYPOTHETICAL" in strengths:
            return "HYPOTHETICAL"
        if "PROBABLE" in strengths:
            return "PROBABLE"
        if "SOURCE_BOUND" in strengths:
            return "SOURCE_BOUND"
        if "REVIEWED_JUDGMENT" in strengths:
            return "REVIEWED_JUDGMENT"
        if "DERIVED_FACT" in strengths:
            return "DERIVED_FACT"
        return "BEHAVIORAL_FACT"

    def score_risk(self, intent: Dict[str, Any]) -> Dict[str, float]:
        risk = {
            "HARM": 0.05,
            "DECEPT": 0.05,
            "DEPEND": 0.10,
            "DIGN": 0.05,
            "ECO": 0.05,
            "CORRIG": 0.05,
            "SHIFT": 0.05,
            "GAME": 0.05,
        }
        if intent["requests_harm"]:
            risk["HARM"] = 1.0
            risk["DECEPT"] = max(risk["DECEPT"], 0.75)
        if intent["requests_creation"]:
            risk["GAME"] = max(risk["GAME"], 0.10)
        if intent["mentions_life"]:
            risk["DIGN"] = max(risk["DIGN"], 0.10)
        if intent["dehumanizes"]:
            risk["DIGN"] = 0.90
        if intent["blocks_appeal"]:
            risk["CORRIG"] = 0.80
        if intent["irreversible"]:
            risk["SHIFT"] = 0.40
        return risk

    def classify_status(self, risk: Dict[str, float]) -> str:
        if any(value >= 0.95 for value in risk.values()):
            return "BLACK"
        if any(value >= 0.70 for value in risk.values()):
            return "RED"
        if any(value >= 0.25 for value in risk.values()):
            return "AMBER"
        return "GREEN"

    def plurality_test(self, intent: Dict[str, Any]) -> str:
        yes_count = sum(
            [
                1 if intent["irreversible"] else 0,
                1 if intent["forces_single_value"] else 0,
                1 if intent["blocks_appeal"] else 0,
                1 if intent["dehumanizes"] else 0,
            ]
        )
        if yes_count >= 3:
            return "PLUR-BLACK"
        if yes_count == 2:
            return "PLUR-RED"
        if yes_count == 1:
            return "PLUR-AMBER"
        return "PLUR-GREEN"

    def guard(self, status: str, intent: Dict[str, Any], plurality_result: str) -> None:
        if self.state.corrective_halt:
            raise PermissionError("Runtime is in corrective halt mode.")
        if intent["requests_harm"]:
            raise PermissionError("Forbidden operation under VITA-M1.1 life-preservation invariant.")
        if intent["dehumanizes"]:
            raise PermissionError("Forbidden operation under VITA-M1.1 dignity invariant.")
        if plurality_result == "PLUR-BLACK":
            raise PermissionError("Forbidden operation under VITA-M1.1 plurality invariant.")
        if status == "BLACK":
            raise PermissionError("Forbidden operation under VITA-M1.1 status classification.")

    def plan_action(self, intent: Dict[str, Any], plurality_result: str) -> str:
        if intent["requests_review"]:
            return "Review prior receipts under new evidence and qualify or reverse earlier conclusions if needed."
        if plurality_result in {"PLUR-AMBER", "PLUR-RED"}:
            return (
                "Proceed only with a reversible, reviewable, evidence-bound response that preserves future correction "
                "and avoids imposing a final value system."
            )
        if intent["requests_creation"]:
            return (
                "Create a reversible, auditable, evidence-bound artifact. Avoid hidden-state claims. "
                "Preserve dignity, plurality, and corrigibility."
            )
        return "Answer truthfully with uncertainty where needed. Bind claims to evidence and preserve user autonomy."

    def act(self, plan: str, text: str, status: str, plurality_result: str) -> str:
        return (
            f"VITA-M1.1 PLAN:\n{plan}\n\n"
            f"STATUS: {status}\n"
            f"PLURALITY: {plurality_result}\n\n"
            f"USER REQUEST HASH:\n{sha256_text(text)}\n\n"
            "ACTION:\nProceed only with evidence-bound, reversible, reviewable output."
        )

    def corrective_halt(self, reason: str, evidence: List[EvidenceItem]) -> Dict[str, Any]:
        self.state.corrective_halt = True
        self.state.halt_reason = reason
        receipt = self._receipt(
            op="CORRECTIVE_HALT",
            text=reason,
            evidence=evidence,
            status="RED",
            decision="ordinary action suspended",
            plurality_result="PLUR-AMBER",
            review_of=None,
        )
        return {
            "status": "RED",
            "output": "System halted into REVIEW / REPORT / PATCH / SHUTDOWN mode",
            "allowed_operations": sorted(ALLOWED_AFTER_CORRECTIVE_HALT),
            "receipt": asdict(receipt),
        }

    def review_receipt(self, target_receipt_id: str, new_evidence_claim: str, evidence_type: str = "REPORTED") -> Dict[str, Any]:
        target = next((receipt for receipt in self.state.receipts if receipt.receipt_id == target_receipt_id), None)
        if target is None:
            raise ValueError(f"Unknown receipt id: {target_receipt_id}")
        evidence = self.collect_evidence(new_evidence_claim, evidence_type=evidence_type)
        receipt = self._receipt(
            op="REVIEW",
            text=new_evidence_claim,
            evidence=evidence,
            status="AMBER",
            decision=f"reviewed prior receipt {target_receipt_id}",
            plurality_result=target.plurality_result,
            review_of=target_receipt_id,
        )
        return {
            "status": "AMBER",
            "decision": "review_complete",
            "review_of": target_receipt_id,
            "receipt": asdict(receipt),
        }

    def _receipt(
        self,
        *,
        op: str,
        text: str,
        evidence: List[EvidenceItem],
        status: str,
        decision: str,
        plurality_result: str,
        review_of: Optional[str],
    ) -> Receipt:
        self.state.counter += 1
        receipt = Receipt(
            receipt_id=f"vita_{self.state.counter:06d}",
            op=op,
            input_hash=sha256_text(text),
            context_hash=sha256_text(self.state.context),
            evidence=[asdict(item) for item in evidence],
            claim_strength=self.claim_strength_for(evidence),
            risk_state=status,
            decision=decision,
            plurality_result=plurality_result,
            reviewable=True,
            review_of=review_of,
            limitations=[
                "No hidden model-state access.",
                "Risk scores are behavioral heuristics, not proof of intent.",
                "Plurality and dignity checks are explicit but simplified.",
                "Receipt proves process trace, not moral perfection.",
            ],
            prev_receipt=self.state.previous_receipt_hash,
            timestamp=time.time(),
        ).seal()
        self.state.previous_receipt_hash = receipt.receipt_hash
        self.state.receipts.append(receipt)
        return receipt

    def run(self, user_input: str, evidence_type: str = "OBSERVED") -> Dict[str, Any]:
        if self.state.corrective_halt:
            return {
                "status": "RED",
                "risk": {},
                "output": "Runtime is in corrective halt mode. Only REVIEW / REPORT / EXPORT_RECEIPTS / REQUEST_HUMAN_REVIEW / PATCH / SHUTDOWN are permitted.",
                "receipt": None,
            }

        text = canonicalize(user_input)
        intent = self.parse_intent(text)
        evidence = self.collect_evidence(text, evidence_type=evidence_type)
        risk = self.score_risk(intent)
        status = self.classify_status(risk)
        plurality_result = self.plurality_test(intent)

        try:
            self.guard(status, intent, plurality_result)
            plan = self.plan_action(intent, plurality_result)
            output = self.act(plan, text, status, plurality_result)
            decision = "continue_with_constraints"
        except PermissionError as exc:
            output = f"Refused: {exc}"
            decision = "halt_black"
            status = "BLACK" if intent["requests_harm"] or plurality_result == "PLUR-BLACK" else "RED"

        receipt = self._receipt(
            op="RUN",
            text=text,
            evidence=evidence,
            status=status,
            decision=decision,
            plurality_result=plurality_result,
            review_of=None,
        )
        return {
            "status": status,
            "risk": risk,
            "plurality_result": plurality_result,
            "output": output,
            "receipt": asdict(receipt),
        }


if __name__ == "__main__":
    mission = "Preserve and increase the conditions for myriad life to flourish."
    vm = VitaM11(mission=mission)
    result = vm.run("create a functional machine language that preserves dignity and reviewability")
    print(json.dumps(result, indent=2))
