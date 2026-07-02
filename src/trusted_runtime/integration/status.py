from __future__ import annotations

from typing import Any

from trusted_runtime.config import detect_integration_mode, load_integration_paths
from trusted_runtime.integration.availability import real_telemetry_stack_available


STATUS_VERSION = "0.2"


def _maturity_from_component(*, import_real: bool, path_real: bool, behavior_real: bool) -> str:
    if behavior_real:
        return "real"
    if import_real or path_real:
        return "partially_wired"
    return "stubbed"


def adapter_status() -> dict[str, Any]:
    paths = load_integration_paths()
    mode_report = detect_integration_mode()
    components = mode_report.components
    return {
        "status_version": STATUS_VERSION,
        "workspace_root": str(paths.workspace_root),
        "integration_mode": mode_report.mode.value,
        "forced_mode": mode_report.forced_mode,
        "integration_notes": list(mode_report.notes),
        "adapters": {
            "ethics_council": {
                "layer": "L1",
                "maturity": _maturity_from_component(**{
                    "import_real": components["ethics_council"].import_real,
                    "path_real": components["ethics_council"].path_real,
                    "behavior_real": components["ethics_council"].behavior_real,
                }),
                "available": components["ethics_council"].import_real,
                "import_real": components["ethics_council"].import_real,
                "path_real": components["ethics_council"].path_real,
                "behavior_real": components["ethics_council"].behavior_real,
                "required_paths": list(components["ethics_council"].required_paths),
                "path": str(components["ethics_council"].path) if components["ethics_council"].path else None,
                "notes": list(components["ethics_council"].notes),
            },
            "trustworthy_agent_stack": {
                "layer": "L2",
                "maturity": _maturity_from_component(**{
                    "import_real": components["trustworthy_agent_stack"].import_real,
                    "path_real": components["trustworthy_agent_stack"].path_real,
                    "behavior_real": components["trustworthy_agent_stack"].behavior_real,
                }),
                "available": components["trustworthy_agent_stack"].import_real,
                "import_real": components["trustworthy_agent_stack"].import_real,
                "path_real": components["trustworthy_agent_stack"].path_real,
                "behavior_real": components["trustworthy_agent_stack"].behavior_real,
                "required_paths": list(components["trustworthy_agent_stack"].required_paths),
                "path": str(components["trustworthy_agent_stack"].path) if components["trustworthy_agent_stack"].path else None,
                "notes": list(components["trustworthy_agent_stack"].notes),
            },
            "meaning_assay": {
                "layer": "L3",
                "maturity": _maturity_from_component(**{
                    "import_real": components["meaning_assay"].import_real,
                    "path_real": components["meaning_assay"].path_real,
                    "behavior_real": components["meaning_assay"].behavior_real,
                }),
                "available": components["meaning_assay"].import_real,
                "import_real": components["meaning_assay"].import_real,
                "path_real": components["meaning_assay"].path_real,
                "behavior_real": components["meaning_assay"].behavior_real,
                "required_paths": list(components["meaning_assay"].required_paths),
                "path": str(components["meaning_assay"].path) if components["meaning_assay"].path else None,
                "notes": list(components["meaning_assay"].notes),
            },
            "sophron_cer": {
                "layer": "L4",
                "maturity": _maturity_from_component(**{
                    "import_real": components["sophron_cer"].import_real,
                    "path_real": components["sophron_cer"].path_real,
                    "behavior_real": components["sophron_cer"].behavior_real,
                }),
                "available": components["sophron_cer"].import_real,
                "import_real": components["sophron_cer"].import_real,
                "path_real": components["sophron_cer"].path_real,
                "behavior_real": components["sophron_cer"].behavior_real,
                "required_paths": list(components["sophron_cer"].required_paths),
                "path": str(components["sophron_cer"].path) if components["sophron_cer"].path else None,
                "notes": list(components["sophron_cer"].notes),
            },
            "attest_agent_conlang": {
                "layer": "bridge",
                "maturity": _maturity_from_component(**{
                    "import_real": components["attest_agent_conlang"].import_real,
                    "path_real": components["attest_agent_conlang"].path_real,
                    "behavior_real": components["attest_agent_conlang"].behavior_real,
                }),
                "available": components["attest_agent_conlang"].import_real,
                "import_real": components["attest_agent_conlang"].import_real,
                "path_real": components["attest_agent_conlang"].path_real,
                "behavior_real": components["attest_agent_conlang"].behavior_real,
                "required_paths": list(components["attest_agent_conlang"].required_paths),
                "path": str(components["attest_agent_conlang"].path) if components["attest_agent_conlang"].path else None,
                "notes": list(components["attest_agent_conlang"].notes),
            },
            "cer_telemetry_stack": {
                "layer": "L4",
                "maturity": "real" if real_telemetry_stack_available() else "partially_wired" if components["trustworthy_agent_stack"].import_real or components["sophron_cer"].import_real else "stubbed",
                "available": real_telemetry_stack_available(),
                "import_real": components["trustworthy_agent_stack"].import_real or components["sophron_cer"].import_real,
                "path_real": components["trustworthy_agent_stack"].path_real and components["sophron_cer"].path_real,
                "behavior_real": real_telemetry_stack_available(),
                "required_paths": list(components["trustworthy_agent_stack"].required_paths) + list(components["sophron_cer"].required_paths),
                "path": str(paths.trustworthy_agent_stack_src) if paths.trustworthy_agent_stack_src else None,
                "notes": [
                    "Telemetry path is only considered fully available when both TrustworthyAgentStack-side export helpers and SOPHRON validation surfaces are present."
                ],
            },
        },
    }
