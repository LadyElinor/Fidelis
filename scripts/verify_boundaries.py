#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "contracts" / "dependency-policy.json"
JS_TS_SUFFIXES = (".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts")
NODE_DEP_FIELDS = ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies")
IMPORT_RE = re.compile(r"(?:import|export)\s+(?:[^;]*?\s+from\s+)?[\"']([^\"']+)[\"']")
REQUIRE_RE = re.compile(r"require\(\s*[\"']([^\"']+)[\"']\s*\)")


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


def discover_import_roots(root: Path, components: set[str]) -> tuple[dict[str, str], dict[str, list[Path]], dict[str, list[Path]]]:
    import_to_component: dict[str, str] = {}
    component_src_roots: dict[str, list[Path]] = defaultdict(list)
    component_test_roots: dict[str, list[Path]] = defaultdict(list)
    packages_dir = root / "packages"
    if not packages_dir.exists():
        return import_to_component, component_src_roots, component_test_roots

    for component in sorted(components):
        component_dir = packages_dir / component
        src_dir = component_dir / "src"
        tests_dir = component_dir / "tests"
        if src_dir.is_dir():
            for child in src_dir.iterdir():
                if child.is_dir() and (child / "__init__.py").exists():
                    import_to_component[child.name] = component
                    component_src_roots[component].append(child)
        if tests_dir.is_dir():
            component_test_roots[component].append(tests_dir)
    return import_to_component, component_src_roots, component_test_roots


def observed_python_edges(component_roots: dict[str, list[Path]], import_to_component: dict[str, str]) -> list[tuple[str, str, Path, str]]:
    observed: list[tuple[str, str, Path, str]] = []
    for component, roots in component_roots.items():
        for package_root in roots:
            for py_file in package_root.rglob("*.py"):
                tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
                for node in ast.walk(tree):
                    module_names: list[str] = []
                    if isinstance(node, ast.Import):
                        module_names = [alias.name for alias in node.names]
                    elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                        module_names = [node.module]
                    for module_name in module_names:
                        top_level = module_name.split(".", 1)[0]
                        target = import_to_component.get(top_level)
                        if target and target != component:
                            observed.append((component, target, py_file, module_name))
    return observed


def discover_node_package_roots(root: Path, components: set[str]) -> tuple[dict[str, str], dict[str, list[Path]], dict[str, list[Path]]]:
    package_name_to_component: dict[str, str] = {}
    component_src_roots: dict[str, list[Path]] = defaultdict(list)
    component_test_roots: dict[str, list[Path]] = defaultdict(list)
    packages_dir = root / "packages"
    if not packages_dir.exists():
        return package_name_to_component, component_src_roots, component_test_roots

    for component in sorted(components):
        component_dir = packages_dir / component
        package_json = component_dir / "package.json"
        if not package_json.exists():
            continue
        package_data = json.loads(package_json.read_text(encoding="utf-8"))
        package_name = package_data.get("name")
        if isinstance(package_name, str) and package_name:
            package_name_to_component[package_name] = component
        src_dir = component_dir / "src"
        tests_dir = component_dir / "tests"
        if src_dir.is_dir():
            component_src_roots[component].append(src_dir)
        if tests_dir.is_dir():
            component_test_roots[component].append(tests_dir)
    return package_name_to_component, component_src_roots, component_test_roots


def observed_js_ts_edges(component_roots: dict[str, list[Path]], package_name_to_component: dict[str, str]) -> list[tuple[str, str, Path, str]]:
    observed: list[tuple[str, str, Path, str]] = []
    for component, roots in component_roots.items():
        for root_dir in roots:
            for file_path in root_dir.rglob("*"):
                if not file_path.is_file() or file_path.suffix not in JS_TS_SUFFIXES:
                    continue
                text = file_path.read_text(encoding="utf-8")
                module_names = IMPORT_RE.findall(text) + REQUIRE_RE.findall(text)
                for module_name in module_names:
                    if module_name.startswith(".") or module_name.startswith("/"):
                        continue
                    package_name = module_name.split("/", 1)[0]
                    if module_name.startswith("@") and module_name.count("/") >= 1:
                        package_name = "/".join(module_name.split("/", 2)[:2])
                    target = package_name_to_component.get(package_name)
                    if target and target != component:
                        observed.append((component, target, file_path, module_name))
    return observed


def observed_node_dependency_edges(root: Path, components: set[str], package_name_to_component: dict[str, str]) -> list[tuple[str, str, Path, str]]:
    observed: list[tuple[str, str, Path, str]] = []
    packages_dir = root / "packages"
    if not packages_dir.exists():
        return observed

    for component in sorted(components):
        package_json = packages_dir / component / "package.json"
        if not package_json.exists():
            continue
        package_data = json.loads(package_json.read_text(encoding="utf-8"))
        for field in NODE_DEP_FIELDS:
            deps = package_data.get(field, {})
            if not isinstance(deps, dict):
                continue
            for package_name in deps:
                target = package_name_to_component.get(package_name)
                if target and target != component:
                    observed.append((component, target, package_json, f"{field}:{package_name}"))
    return observed


def build_policy_graphs(components: dict[str, dict[str, object]]) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    graph: dict[str, set[str]] = {}
    test_graph: dict[str, set[str]] = {}
    known_components = set(components)

    for name, details in components.items():
        may_depend_on = details.get("may_depend_on", [])
        test_may_depend_on = details.get("test_may_depend_on", [])

        if not isinstance(may_depend_on, list):
            raise ValueError(f"component {name!r} has non-list may_depend_on")
        if not isinstance(test_may_depend_on, list):
            raise ValueError(f"component {name!r} has non-list test_may_depend_on")
        if len(may_depend_on) != len(set(may_depend_on)):
            raise ValueError(f"component {name!r} has duplicate may_depend_on entries")
        if len(test_may_depend_on) != len(set(test_may_depend_on)):
            raise ValueError(f"component {name!r} has duplicate test_may_depend_on entries")

        may_set = set(may_depend_on)
        test_set = set(test_may_depend_on)
        unknown_may = sorted(dep for dep in may_set if dep not in known_components)
        unknown_test = sorted(dep for dep in test_set if dep not in known_components)
        if unknown_may:
            raise ValueError(f"component {name!r} references unknown may_depend_on target(s): {', '.join(unknown_may)}")
        if unknown_test:
            raise ValueError(f"component {name!r} references unknown test_may_depend_on target(s): {', '.join(unknown_test)}")

        graph[name] = may_set
        test_graph[name] = may_set | test_set

    return graph, test_graph


def main() -> int:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    components = policy["components"]
    try:
        graph, test_graph = build_policy_graphs(components)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

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

    import_to_component, component_src_roots, component_test_roots = discover_import_roots(ROOT, set(graph))
    src_violations: list[str] = []
    src_edges = observed_python_edges(component_src_roots, import_to_component)
    for source, target, py_file, module_name in src_edges:
        if target not in graph.get(source, set()):
            src_violations.append(
                f"observed forbidden Python import: {source} -> {target} via {py_file.relative_to(ROOT)} ({module_name})"
            )

    if src_violations:
        for violation in src_violations:
            print(f"ERROR: {violation}", file=sys.stderr)
        return 1

    print(f"Declared dependency policy valid: {len(graph)} components, acyclic.")
    if component_src_roots:
        print(f"Observed Python src imports are within declared dependency policy ({len(src_edges)} cross-component edges checked).")
    else:
        print("Observed Python src imports were not checked because no local package src roots were found.")

    test_edges = observed_python_edges(component_test_roots, import_to_component)
    test_violations: list[str] = []
    for source, target, py_file, module_name in test_edges:
        if target not in test_graph.get(source, set()):
            test_violations.append(
                f"observed forbidden Python test import: {source} -> {target} via {py_file.relative_to(ROOT)} ({module_name})"
            )

    if test_violations:
        for violation in test_violations:
            print(f"ERROR: {violation}", file=sys.stderr)
        return 1

    if component_test_roots:
        print(f"Observed Python test imports are within explicit test policy ({len(test_edges)} cross-component edges checked).")
    else:
        print("Observed Python test imports were not checked because no package tests directories were found.")

    node_package_names, node_src_roots, node_test_roots = discover_node_package_roots(ROOT, set(graph))
    node_src_edges = observed_js_ts_edges(node_src_roots, node_package_names)
    node_src_violations: list[str] = []
    for source, target, file_path, module_name in node_src_edges:
        if target not in graph.get(source, set()):
            node_src_violations.append(
                f"observed forbidden JS/TS import: {source} -> {target} via {file_path.relative_to(ROOT)} ({module_name})"
            )
    if node_src_violations:
        for violation in node_src_violations:
            print(f"ERROR: {violation}", file=sys.stderr)
        return 1

    node_dependency_edges = observed_node_dependency_edges(ROOT, set(graph), node_package_names)
    node_dependency_violations: list[str] = []
    for source, target, file_path, detail in node_dependency_edges:
        if target not in graph.get(source, set()):
            node_dependency_violations.append(
                f"observed forbidden package.json dependency: {source} -> {target} via {file_path.relative_to(ROOT)} ({detail})"
            )
    if node_dependency_violations:
        for violation in node_dependency_violations:
            print(f"ERROR: {violation}", file=sys.stderr)
        return 1

    if node_src_roots:
        print(f"Observed JS/TS src imports are within declared dependency policy ({len(node_src_edges)} cross-component edges checked).")
    else:
        print("Observed JS/TS src imports were not checked because no local Node package src roots were found.")

    if node_package_names:
        print(f"Observed package.json dependencies are within declared dependency policy ({len(node_dependency_edges)} cross-component edges checked).")
    else:
        print("Observed package.json dependencies were not checked because no local Node packages were found.")

    node_test_edges = observed_js_ts_edges(node_test_roots, node_package_names)
    node_test_violations: list[str] = []
    for source, target, file_path, module_name in node_test_edges:
        if target not in test_graph.get(source, set()):
            node_test_violations.append(
                f"observed forbidden JS/TS test import: {source} -> {target} via {file_path.relative_to(ROOT)} ({module_name})"
            )
    if node_test_violations:
        for violation in node_test_violations:
            print(f"ERROR: {violation}", file=sys.stderr)
        return 1

    if node_test_roots:
        print(f"Observed JS/TS test imports are within explicit test policy ({len(node_test_edges)} cross-component edges checked).")
    else:
        print("Observed JS/TS test imports were not checked because no local Node package tests directories were found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
