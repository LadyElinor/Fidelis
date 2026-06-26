from __future__ import annotations

from typing import Any

from trusted_runtime.config import load_integration_paths
from trusted_runtime.integration.availability import (
    ethics_council_available,
    meaning_assay_available,
    real_telemetry_stack_available,
    sophron_cer_available,
    trustworthy_agent_stack_available,
)


STATUS_VERSION = "0.1"


def _integration_mode(*, ethics: bool, meaning: bool, tas: bool, sophron: bool) -> str:
    available = [ethics, meaning, tas, sophron]
    if all(available):
        return "all-real"
    if any(available):
        return "partial"
    return "stub"


def adapter_status() -> dict[str, Any]:
    paths = load_integration_paths()
    ethics = ethics_council_available()
    meaning = meaning_assay_available()
    tas = trustworthy_agent_stack_available()
    sophron = sophron_cer_available()
    return {
        "status_version": STATUS_VERSION,
        "workspace_root": str(paths.workspace_root),
        "integration_mode": _integration_mode(ethics=ethics, meaning=meaning, tas=tas, sophron=sophron),
        "adapters": {
            "ethics_council": {
                "layer": "L1",
                "maturity": "real" if ethics else "unavailable",
                "available": ethics,
                "path": str(paths.ethics_council_src) if paths.ethics_council_src else None,
                "notes": [
                    "Real adapter when local source is importable via ETHICS_COUNCIL_SRC or workspace fallback."
                ],
            },
            "trustworthy_agent_stack": {
                "layer": "L2",
                "maturity": "partially_wired" if tas else "stubbed",
                "available": tas,
                "path": str(paths.trustworthy_agent_stack_src) if paths.trustworthy_agent_stack_src else None,
                "notes": [
                    "Bridge uses local minimal MCP demo / hash utilities when available; full enforcement closure remains incomplete."
                ],
            },
            "meaning_assay": {
                "layer": "L3",
                "maturity": "real" if meaning else "unavailable",
                "available": meaning,
                "path": str(paths.meaning_assay_src) if paths.meaning_assay_src else None,
                "notes": [
                    "Real adapter when meaning-assay source is importable; arbitrary action mapping still uses heuristic case translation."
                ],
            },
            "sophron_cer": {
                "layer": "L4",
                "maturity": "partially_wired" if sophron else "stubbed",
                "available": sophron,
                "path": str(paths.sophron_cer_src) if paths.sophron_cer_src else None,
                "notes": [
                    "Validation bridge can run against local SOPHRON assets when present, but evidence closure remains uneven."
                ],
            },
            "cer_telemetry_stack": {
                "layer": "L4",
                "maturity": "realish" if real_telemetry_stack_available() else "partially_wired" if tas or sophron else "stubbed",
                "available": real_telemetry_stack_available(),
                "path": str(paths.trustworthy_agent_stack_src) if paths.trustworthy_agent_stack_src else None,
                "notes": [
                    "Telemetry path is only considered fully available when both TrustworthyAgentStack-side export helpers and SOPHRON validation surfaces are present."
                ],
            },
        },
    }
