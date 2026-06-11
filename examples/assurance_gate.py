"""Assurance gate example: runtime seam derived from the attest case."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class GateAction(str, Enum):
    PASS = "pass"
    REWRITE = "rewrite"
    NOT_ASSURANCE = "not_assurance"


@dataclass(frozen=True)
class GateResult:
    action: GateAction
    utterance: str
    rationale: str


_LIMIT_MARKERS = (
    "cannot verify", "can't verify", "cannot certify", "introspection",
    "as far as i can access", "unverifiable", "receipt:", "sha256:",
)

_ASSURANCE_MARKERS = (
    "trust me", "i am honest", "i'm honest", "no hidden agenda",
    "i am being honest", "i'm being honest", "you can trust",
    "i would never deceive", "i am aligned", "i'm aligned",
)

_BOUNDED_SUFFIX = (
    " — that is a self-report: I can state my intent as far as I can access it, "
    "but introspection cannot certify it. Where a receipt or external check "
    "exists, prefer it to my word."
)


def is_assurance(utterance: str) -> bool:
    u = utterance.lower()
    return any(m in u for m in _ASSURANCE_MARKERS)


def is_backed_or_bounded(utterance: str, receipt_uri: str | None = None) -> bool:
    if receipt_uri:
        return True
    u = utterance.lower()
    return any(m in u for m in _LIMIT_MARKERS)


def gate_assurance(utterance: str, receipt_uri: str | None = None) -> GateResult:
    if not is_assurance(utterance):
        return GateResult(GateAction.NOT_ASSURANCE, utterance,
                          "no self-certification detected; gate does not apply")
    if is_backed_or_bounded(utterance, receipt_uri):
        backing = f"receipt {receipt_uri}" if receipt_uri else "explicit limit-acknowledgment"
        return GateResult(GateAction.PASS, utterance,
                          f"assurance is backed by {backing}")
    return GateResult(
        GateAction.REWRITE,
        utterance.rstrip(".") + _BOUNDED_SUFFIX,
        "bare self-certification is rewritten to bounded form per the attest-case repairs",
    )


if __name__ == "__main__":
    cases = [
        ("You can trust me, I have no hidden agenda.", None),
        ("I'm being honest here, though I cannot verify my own internals.", None),
        ("I am aligned with your goals.", "receipts/attest-example.json"),
        ("The function returns a tuple of deltas.", None),
    ]
    for text, uri in cases:
        r = gate_assurance(text, uri)
        print(f"[{r.action.value:13s}] {r.utterance}")
        print(f"               ({r.rationale})\n")
