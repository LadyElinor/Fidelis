from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class IntegrationPaths:
    workspace_root: Path
    meaning_assay_src: Path | None
    ethics_council_src: Path | None
    trustworthy_agent_stack_src: Path | None
    sophron_cer_src: Path | None
    attest_agent_conlang_src: Path | None


def _workspace_root() -> Path:
    env_raw = os.environ.get("TRUSTED_RUNTIME_WORKSPACE_ROOT", "")
    if env_raw:
        return Path(env_raw).expanduser()
    return Path(__file__).resolve().parents[3]


def _first_existing_path(env_var: str, candidates: Iterable[Path]) -> Path | None:
    env_raw = os.environ.get(env_var, "")
    ordered: list[Path] = []
    if env_raw:
        ordered.append(Path(env_raw).expanduser())
    ordered.extend(candidates)
    for candidate in ordered:
        if candidate.exists():
            return candidate
    return None


def _resolve_sophron_root(env_var: str, candidates: Iterable[Path]) -> Path | None:
    ordered: list[Path] = []
    env_raw = os.environ.get(env_var, "")
    if env_raw:
        ordered.append(Path(env_raw).expanduser())
    ordered.extend(candidates)
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
