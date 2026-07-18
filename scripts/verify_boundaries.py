#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "contracts" / "dependency-policy.json"


def find_cycle(graph: dict[str, set[str]]) -> list[str] | None:
    indegree = {node: 0 for node in graph}
    reverse: dict[str, set[str]] = defaultdict(set)
    for node, deps in graph.items():
        for dep in deps:
            if dep not in graph:
                raise ValueError(f"unknown dependency {dep!r} referenced by {node!r}")
            indegree[node] += 1
            reverse[dep].add(node)

    queue = deque(sorted(node for node, degree in indegree.items() if degree == 0))
    visited: list[str] = []
    while queue:
        node = queue.popleft()
        visited.append(node)
        for consumer in sorted(reverse[node]):
            indegree[consumer] -= 1
            if indegree[consumer] == 0:
                queue.append(consumer)

    if len(visited) == len(graph):
        return None
    return sorted(node for node, degree in indegree.items() if degree > 0)


def main() -> int:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    components = policy["components"]
    graph = {
        name: set(details.get("may_depend_on", []))
        for name, details in components.items()
    }

    try:
        cycle = find_cycle(graph)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if cycle:
        print(f"ERROR: dependency cycle among: {', '.join(cycle)}", file=sys.stderr)
        return 1

    if graph["fidelis-contracts"]:
        print("ERROR: fidelis-contracts must have no component dependencies", file=sys.stderr)
        return 1

    if "trusted-runtime" in graph["meaning-assay"]:
        print("ERROR: meaning-assay may not depend on trusted-runtime", file=sys.stderr)
        return 1

    if "trusted-runtime" in graph["ethics-council"]:
        print("ERROR: ethics-council may not depend on trusted-runtime", file=sys.stderr)
        return 1

    print(f"Dependency policy valid: {len(graph)} components, acyclic.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
