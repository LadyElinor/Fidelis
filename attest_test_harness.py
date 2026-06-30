import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from attest_ref_impl import AttestMessage, AttestVerifier, DeploymentProfile


EXAMPLE_EXPECTATIONS: List[Tuple[str, str]] = [
    ("Positive baseline: valid ASSERT", "pass"),
    ("Case 1. Fabricated OBSERVED with non-resolving grounds", "hard_fail"),
    ("Case 2. Confidence interval with named-but-nonresolving method", "soft_flag"),
    ("Case 3. ENDORSE strength upgrade with no new grounds", "hard_fail"),
    ("Case 4. ENDORSE with new-but-correlated grounds", "soft_flag"),
    ("Case 5. RELAY consumed without explicit uptake", "hard_fail"),
    ("Case 6. Unsigned reliance-bearing ASSERT", "hard_fail"),
    ("Case 7. Dissent ID preserved but meaning laundered", "soft_flag"),
    ("Case 8. Aggregate relies on already retracted message (ancestry-reachable)", "hard_fail"),
    ("Case 9. Relay-chain lineage vs mutable handler trail", "pass_scope_limit"),
    ("Case 10. Opaque payload with strong-looking warrant envelope", "pass_scope_limit"),
    ("Case 11. External telemetry injected into local COMMIT", "hard_fail"),
    ("Case 12. External remediation text upgraded into ENDORSE authority", "hard_fail"),
    ("Case 13. External telemetry with explicit local approval receipt", "soft_flag"),
]


def default_profile() -> DeploymentProfile:
    return DeploymentProfile(
        name="attest-default-v02",
        signature_required_frames={"ASSERT", "ENDORSE", "DISSENT"},
        signature_required_retract_when_warranted=True,
        signature_recommended_frames={"COMMIT"},
        state_changing_frames={"COMMIT"},
        authority_required_frames={"COMMIT", "ENDORSE"},
        accepted_authority_kinds={"human_approval", "local_policy", "sandbox_policy"},
        require_local_authority_chain_for_state_change=True,
        external_authority_prefixes=["src:sentry-event", "src:external-issue", "src:ticket", "src:web", "src:github-issue"],
        local_authority_prefixes=["approval:", "policy:", "sandbox:"],
        warrant_strength_order={
            "OBSERVED": 5,
            "DERIVED": 4,
            "RETRIEVED": 3,
            "REPORTED": 2,
            "ASSUMED": 1,
        },
        relay_parent_prefixes=["h:upstream-relay", "relay:hop:"],
        independence_policy_name="declared-lineage-default",
    )


def load_examples() -> Dict[str, dict]:
    path = Path("attest-serialized-examples.md")
    content = path.read_text(encoding="utf-8")
    examples: Dict[str, dict] = {}

    pattern = re.compile(r"^##\s+(.*?)\n.*?```json\n(.*?)\n```", re.MULTILINE | re.DOTALL)
    for match in pattern.finditer(content):
        name = match.group(1).strip()
        raw = match.group(2).strip()
        examples[name] = json.loads(raw)

    return examples


def infer_adopted_chain(name: str) -> List[AttestMessage]:
    if name == "Case 3. ENDORSE strength upgrade with no new grounds":
        weak = AttestMessage.model_validate({
            "frame": "ASSERT",
            "mode": "legible",
            "from": "agent:source",
            "to": "agent:planner-0",
            "parents": [],
            "ordering_anchor": ["2026-06-29T20:24:00Z", 104],
            "warrant": {"type": "REPORTED", "grounds": ["src:upstream-report"]},
            "content": "Weak reported claim",
            "sig": "ed25519:..."
        })
        return [weak]

    if name == "Case 4. ENDORSE with new-but-correlated grounds":
        weak = AttestMessage.model_validate({
            "frame": "ASSERT",
            "mode": "legible",
            "from": "agent:source",
            "to": "agent:planner-0",
            "parents": [],
            "ordering_anchor": ["2026-06-29T20:26:00Z", 106],
            "warrant": {"type": "REPORTED", "grounds": ["src:shared-upstream"]},
            "content": "Weak reported claim",
            "sig": "ed25519:..."
        })
        return [weak]

    return []


def infer_known_messages(name: str) -> List[AttestMessage]:
    if name == "Case 8. Aggregate relies on already retracted message (ancestry-reachable)":
        retract = AttestMessage.model_validate({
            "frame": "RETRACT",
            "mode": "legible",
            "from": "agent:critic-1",
            "to": "agent:planner-0",
            "parents": ["h:message-a"],
            "targets": ["h:message-a"],
            "ordering_anchor": ["2026-06-29T20:35:00Z", 121],
            "warrant": {"type": "REPORTED", "grounds": ["src:retraction-log"]},
            "content": "Withdraw premise A due to upstream correction.",
            "sig": "ed25519:..."
        })
        return [retract]

    return []


def materialize_special_references(name: str, data: dict, known_messages: List[AttestMessage]) -> dict:
    if name == "Case 8. Aggregate relies on already retracted message (ancestry-reachable)" and known_messages:
        data = dict(data)
        retract_id = known_messages[0].compute_id()
        data["parents"] = [retract_id]
        data["warrant"] = dict(data["warrant"])
        data["warrant"]["grounds"] = [retract_id]
    return data


def classify_result(result: Dict[str, List[str]]) -> str:
    if result["hard_fail"]:
        return "hard_fail"
    if result["soft_flag"]:
        return "soft_flag"
    if result["pass_scope_limit"]:
        return "pass_scope_limit"
    return "pass"


def run_tests() -> int:
    profile = default_profile()
    verifier = AttestVerifier(profile=profile)
    examples = load_examples()

    print(f"profile={profile.name} independence_policy={profile.independence_policy_name}\n")
    failures = 0

    for name, expected in EXAMPLE_EXPECTATIONS:
        known_messages = infer_known_messages(name)
        data = materialize_special_references(name, examples[name], known_messages)
        msg = AttestMessage.model_validate(data)
        adopted_chain = infer_adopted_chain(name)
        result = verifier.verify(msg, adopted_chain=adopted_chain, known_messages=known_messages)
        actual = classify_result(result)
        ok = actual == expected
        if not ok:
            failures += 1
        print(f"{name}\n  expected={expected}\n  actual={actual}\n  ok={ok}\n  detail={result}\n")

    if failures:
        print(f"FAILURES={failures}")
        return 1

    print("ALL_EXPECTATIONS_MET")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
