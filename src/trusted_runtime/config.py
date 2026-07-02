from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable


class IntegrationMode(str, Enum):
    STUB = "stub"
    PARTIAL = "partial"
    ALL_REAL = "all-real"


@dataclass(frozen=True)
class IntegrationPaths:
    workspace_root: Path
    meaning_assay_src: Path | None
    ethics_council_src: Path | None
    trustworthy_agent_stack_src: Path | None
    sophron_cer_src: Path | None
    attest_agent_conlang_src: Path | None


@dataclass(frozen=True)
class IntegrationComponentStatus:
    name: str
    import_real: bool
    path_real: bool
    behavior_real: bool
    path: Path | None = None
    required_paths: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class IntegrationModeReport:
    mode: IntegrationMode
    forced_mode: str | None
    components: dict[str, IntegrationComponentStatus] = field(default_factory=dict)
    notes: tuple[str, ...] = ()


def _workspace_root() -> Path:
    env_raw = os.environ.get("TRUSTED_RUNTIME_WORKSPACE_ROOT", "")
    if env_raw:
        return Path(env_raw).expanduser()
    return Path(__file__).resolve().parents[3]


def _ordered_candidates(env_var: str, candidates: Iterable[Path]) -> list[Path]:
    env_raw = os.environ.get(env_var, "")
    ordered: list[Path] = []
    if env_raw:
        ordered.append(Path(env_raw).expanduser())
    ordered.extend(candidates)
    return ordered


def _first_existing_path(env_var: str, candidates: Iterable[Path]) -> Path | None:
    for candidate in _ordered_candidates(env_var, candidates):
        if candidate.exists():
            return candidate
    return None


def _resolve_sophron_root(env_var: str, candidates: Iterable[Path]) -> Path | None:
    ordered = _ordered_candidates(env_var, candidates)
    for candidate in ordered:
        if not candidate.exists():
            continue
        if (candidate / "examples" / "adapter_from_cer_v01_receipts.js").exists():
            return candidate
        if (candidate / "adapters" / "cer_telemetry" / "from_v0_1_receipts.js").exists():
            return candidate
    for candidate in ordered:
        if candidate.exists():
            return candidate
    return None


def _has_required_paths(root: Path | None, required_paths: Iterable[str]) -> bool:
    if root is None:
        return False
    return all((root / rel).exists() for rel in required_paths)


def load_integration_paths() -> IntegrationPaths:
    root = _workspace_root()
    meaning_assay_src = _first_existing_path(
        "MEANING_ASSAY_SRC",
        [root / "27assay" / "meaning-assay" / "src"],
    )
    ethics_council_src = _first_existing_path(
        "ETHICS_COUNCIL_SRC",
        [root / "EthicsCouncil"],
    )
    trustworthy_agent_stack_src = _first_existing_path(
        "TRUSTWORTHY_AGENT_STACK_SRC",
        [
            root / "repos" / "TrustworthyAgentStack-clean",
            root / "repos" / "TrustworthyAgentStack",
        ],
    )
    sophron_cer_src = _resolve_sophron_root(
        "SOPHRON_CER_SRC",
        [
            root / "repos" / "SOPHRON-CER-clean",
            Path.home() / "Molt" / "workspace" / "repos" / "SOPHRON-CER",
            root / "repos" / "SOPHRON-CER",
        ],
    )
    attest_agent_conlang_src = _first_existing_path(
        "ATTEST_AGENT_CONLANG_SRC",
        [root / "AttestAgentConlang"],
    )
    return IntegrationPaths(
        workspace_root=root,
        meaning_assay_src=meaning_assay_src,
        ethics_council_src=ethics_council_src,
        trustworthy_agent_stack_src=trustworthy_agent_stack_src,
        sophron_cer_src=sophron_cer_src,
        attest_agent_conlang_src=attest_agent_conlang_src,
    )


def detect_integration_mode() -> IntegrationModeReport:
    paths = load_integration_paths()
    forced_mode = os.environ.get("TRUSTED_RUNTIME_MODE") or None

    try:
        from trusted_runtime.integration.availability import (
            ethics_council_available,
            meaning_assay_available,
            real_telemetry_stack_available,
            sophron_cer_available,
            trustworthy_agent_stack_available,
        )
    except Exception as exc:
        return IntegrationModeReport(
            mode=IntegrationMode.STUB,
            forced_mode=forced_mode,
            components={},
            notes=(f"availability-import-failed:{type(exc).__name__}",),
        )

    components = {
        "ethics_council": IntegrationComponentStatus(
            name="ethics_council",
            import_real=ethics_council_available(),
            path_real=_has_required_paths(paths.ethics_council_src, ("efm_council.py",)),
            behavior_real=ethics_council_available() and _has_required_paths(paths.ethics_council_src, ("efm_council.py",)),
            path=paths.ethics_council_src,
            required_paths=("efm_council.py",),
            notes=("Counts as REAL only when import and required-path checks both succeed.",),
        ),
        "meaning_assay": IntegrationComponentStatus(
            name="meaning_assay",
            import_real=meaning_assay_available(),
            path_real=_has_required_paths(paths.meaning_assay_src, ("meaning_assay",)),
            behavior_real=meaning_assay_available() and _has_required_paths(paths.meaning_assay_src, ("meaning_assay",)),
            path=paths.meaning_assay_src,
            required_paths=("meaning_assay",),
            notes=("Heuristic case translation does not reduce import/path truthfulness, but richer behavior closure remains separate.",),
        ),
        "trustworthy_agent_stack": IntegrationComponentStatus(
            name="trustworthy_agent_stack",
            import_real=trustworthy_agent_stack_available(),
            path_real=_has_required_paths(paths.trustworthy_agent_stack_src, (
                "examples/minimal_mcp_agent/hash_utils.py",
                "examples/minimal_mcp_agent/mock_ethics_council.py",
                "scripts/route_task.py",
            )),
            behavior_real=real_telemetry_stack_available(),
            path=paths.trustworthy_agent_stack_src,
            required_paths=(
                "examples/minimal_mcp_agent/hash_utils.py",
                "examples/minimal_mcp_agent/mock_ethics_council.py",
                "scripts/route_task.py",
            ),
            notes=("Behavior-real remains false until the runtime exercises the real TAS helper stack rather than fallback heuristics alone.",),
        ),
        "sophron_cer": IntegrationComponentStatus(
            name="sophron_cer",
            import_real=sophron_cer_available(),
            path_real=_has_required_paths(paths.sophron_cer_src, (
                "examples/adapter_from_cer_v01_receipts.js",
            )) or _has_required_paths(paths.sophron_cer_src, (
                "adapters/cer_telemetry/from_v0_1_receipts.js",
            )),
            behavior_real=sophron_cer_available() and (
                _has_required_paths(paths.sophron_cer_src, ("examples/adapter_from_cer_v01_receipts.js",))
                or _has_required_paths(paths.sophron_cer_src, ("adapters/cer_telemetry/from_v0_1_receipts.js",))
            ),
            path=paths.sophron_cer_src,
            required_paths=(
                "examples/adapter_from_cer_v01_receipts.js OR adapters/cer_telemetry/from_v0_1_receipts.js",
            ),
            notes=("SOPHRON path-real requires a known adapter entrypoint, not mere repo presence.",),
        ),
        "attest_agent_conlang": IntegrationComponentStatus(
            name="attest_agent_conlang",
            import_real=paths.attest_agent_conlang_src is not None,
            path_real=_has_required_paths(paths.attest_agent_conlang_src, ("attest_ref_impl.py",)),
            behavior_real=(paths.attest_agent_conlang_src is not None) and _has_required_paths(paths.attest_agent_conlang_src, ("attest_ref_impl.py",)),
            path=paths.attest_agent_conlang_src,
            required_paths=("attest_ref_impl.py",),
            notes=("Bridge behavior-real here means the real verifier root is structurally available to the runtime seam.",),
        ),
    }

    behavior_flags = [component.behavior_real for component in components.values()]
    if all(behavior_flags):
        mode = IntegrationMode.ALL_REAL
    elif any(component.import_real or component.path_real or component.behavior_real for component in components.values()):
        mode = IntegrationMode.PARTIAL
    else:
        mode = IntegrationMode.STUB

    notes: list[str] = []
    if forced_mode:
        notes.append(f"forced-mode-requested:{forced_mode}")
        notes.append("detected_mode remains computed and is not overridden by the request")

    return IntegrationModeReport(
        mode=mode,
        forced_mode=forced_mode,
        components=components,
        notes=tuple(notes),
    )
