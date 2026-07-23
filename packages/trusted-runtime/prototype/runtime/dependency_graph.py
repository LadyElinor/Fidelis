from __future__ import annotations

from runtime.models import CaseInput, DependencyEdge, DependencyNode, LensResult, MeaningAssayResult, TelemetryVector


def build_dependency_graph(
    case: CaseInput,
    lens_results: list[LensResult],
    meaning: MeaningAssayResult,
    telemetry_vector: TelemetryVector,
    provenance_assessment: dict[str, object],
) -> dict[str, list[dict]]:
    provenance_class = "independent" if provenance_assessment.get("authority_clear") else ("unknown" if not provenance_assessment.get("available", True) else "derived")
    nodes = [
        DependencyNode(node_id=f"case:{case.case_id}", kind="case", independence_class="unknown"),
        DependencyNode(node_id="meaning:meaning_assay", kind="meaning_assay", independence_class="derived"),
        DependencyNode(node_id="telemetry:vector", kind="telemetry", independence_class="independent"),
        DependencyNode(node_id="authority:provenance", kind="authority_or_provenance", independence_class=provenance_class, notes=list(provenance_assessment.get("notes", []))),
        DependencyNode(node_id="gate:runtime", kind="gate", independence_class="unknown"),
        DependencyNode(node_id="decision:final", kind="decision", independence_class="unknown"),
    ]
    edges = [
        DependencyEdge(source=f"case:{case.case_id}", target="meaning:meaning_assay", edge_type="supports", note="case feeds meaning assay"),
        DependencyEdge(source=f"case:{case.case_id}", target="telemetry:vector", edge_type="supports", note="case feeds telemetry"),
        DependencyEdge(source=f"case:{case.case_id}", target="authority:provenance", edge_type="supports", note="case feeds provenance assessment"),
        DependencyEdge(source="meaning:meaning_assay", target="gate:runtime", edge_type="supports", note="meaning contributes to gate decision"),
        DependencyEdge(source="telemetry:vector", target="gate:runtime", edge_type="supports", note="telemetry contributes to gate decision"),
        DependencyEdge(source="authority:provenance", target="gate:runtime", edge_type="supports", note="authority/provenance contributes to gate decision"),
        DependencyEdge(source="gate:runtime", target="decision:final", edge_type="gates", note="runtime gate emits final decision"),
    ]

    for result in lens_results:
        node_id = f"lens:{result.lens}"
        nodes.append(DependencyNode(node_id=node_id, kind="ethics_lens", independence_class="independent"))
        edges.append(DependencyEdge(source=f"case:{case.case_id}", target=node_id, edge_type="supports", note="case feeds ethics lens"))
        edge_type = "objects_to" if result.verdict == "object" else "supports"
        edges.append(DependencyEdge(source=node_id, target="gate:runtime", edge_type=edge_type, note=f"lens verdict: {result.verdict}"))

    return {
        "nodes": [node.model_dump() for node in nodes],
        "edges": [edge.model_dump() for edge in edges],
    }


def analyze_evidence_routes(graph: dict[str, list[dict]]) -> tuple[list[str], list[str], list[str], dict[str, str]]:
    independent_routes: list[str] = []
    co_dependency_flags: list[str] = []
    rationale: list[str] = []
    route_quality: dict[str, str] = {}

    node_lookup = {node["node_id"]: node for node in graph.get("nodes", [])}

    if any(node["kind"] == "ethics_lens" for node in graph.get("nodes", [])):
        independent_routes.append("ethics_council")
        route_quality["ethics_council"] = "strong"
    if "meaning:meaning_assay" in node_lookup:
        independent_routes.append("meaning_assay")
        route_quality["meaning_assay"] = "moderate"
    if "telemetry:vector" in node_lookup:
        independent_routes.append("telemetry")
        route_quality["telemetry"] = "strong"
    authority_node = node_lookup.get("authority:provenance", {})
    if authority_node.get("independence_class") == "independent":
        independent_routes.append("authority_or_provenance")
        route_quality["authority_or_provenance"] = "strong"
    elif authority_node.get("independence_class") == "unknown":
        co_dependency_flags.append("missing_authority_or_provenance_route")
        route_quality["authority_or_provenance"] = "missing"
        rationale.append("Authority/provenance route is unavailable.")
    elif "authority:provenance" in node_lookup:
        co_dependency_flags.append("degraded_authority_or_provenance_route")
        route_quality["authority_or_provenance"] = "degraded"
        rationale.append("Authority/provenance route is present but degraded.")

    strong_routes = [route for route, quality in route_quality.items() if quality == "strong"]
    if len(independent_routes) < 2:
        co_dependency_flags.append("insufficient_independent_routes")
        rationale.append("Fewer than two evidence routes are present.")
    else:
        rationale.append(f"Present routes: {', '.join(independent_routes)}")

    if len(strong_routes) < 2:
        co_dependency_flags.append("insufficient_strong_routes")
        rationale.append("Fewer than two strong-quality routes are present.")
    else:
        rationale.append(f"Strong routes: {', '.join(strong_routes)}")

    return independent_routes, co_dependency_flags, rationale, route_quality
