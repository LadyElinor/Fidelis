from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict


PICOBOT_HINTS = {
    "remind",
    "reminder",
    "heartbeat",
    "telegram",
    "status",
    "check",
    "fetch",
    "append",
    "note",
    "log",
    "ping",
}

OPENCLAW_HINTS = {
    "research",
    "compare",
    "refactor",
    "architecture",
    "investigate",
    "synthesize",
    "integration",
    "contract",
    "governance",
    "safety",
    "multi-step",
    "repo",
    "repository",
    "codebase",
}

NEVER_AUTO_HINTS = {
    "production",
    "credentials",
    "secret",
    "delete",
    "destroy",
    "message this person",
    "post publicly",
    "rotate",
    "deploy",
    "legal",
    "compliance",
}


@dataclass
class RoutingDecision:
    route: str
    confidence: str
    reasons: list[str]


def classify_task(task: str) -> RoutingDecision:
    text = task.strip().lower()
    reasons: list[str] = []

    for hint in NEVER_AUTO_HINTS:
        if hint in text:
            reasons.append(f"matched never-auto hint: {hint}")
            return RoutingDecision(route="never_auto_route", confidence="high", reasons=reasons)

    openclaw_hits = sorted(h for h in OPENCLAW_HINTS if h in text)
    picobot_hits = sorted(h for h in PICOBOT_HINTS if h in text)

    if openclaw_hits:
        reasons.extend([f"matched OpenClaw hint: {h}" for h in openclaw_hits])
    if picobot_hits:
        reasons.extend([f"matched Picobot hint: {h}" for h in picobot_hits])

    if openclaw_hits and not picobot_hits:
        return RoutingDecision(route="openclaw", confidence="medium", reasons=reasons)

    if picobot_hits and not openclaw_hits:
        complexity_signals = len(re.findall(r"\band\b|\bthen\b|\balso\b", text))
        if complexity_signals > 1:
            reasons.append("multiple-step conjunctions detected, routing upward")
            return RoutingDecision(route="openclaw", confidence="medium", reasons=reasons)
        return RoutingDecision(route="picobot", confidence="medium", reasons=reasons)

    if openclaw_hits and picobot_hits:
        reasons.append("mixed low-cost and high-context signals detected, routing upward")
        return RoutingDecision(route="openclaw", confidence="medium", reasons=reasons)

    reasons.append("no strong hints matched, defaulting upward on uncertainty")
    return RoutingDecision(route="openclaw", confidence="low", reasons=reasons)


def main() -> int:
    parser = argparse.ArgumentParser(description="Route a task to Picobot, OpenClaw, or never-auto-route.")
    parser.add_argument("task", help="Task description to classify")
    args = parser.parse_args()

    decision = classify_task(args.task)
    print(json.dumps(asdict(decision), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
