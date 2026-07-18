from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from trusted_runtime.export import export_decision_payload
from trusted_runtime.integration.engine import assemble_execution_decision
from trusted_runtime.integration.report import render_markdown_report
from trusted_runtime.shared.models import ProposedAction


def load_review_input(path: Path) -> ProposedAction:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ProposedAction.model_validate(payload)


def run_review_input(input_path: Path, output_dir: Path) -> ProposedAction:
    action = load_review_input(input_path)
    decision = assemble_execution_decision(action)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "decision_output.json").write_text(json.dumps(export_decision_payload(decision), indent=2), encoding="utf-8")
    (output_dir / "decision_report.md").write_text(render_markdown_report(decision), encoding="utf-8")
    return action


def build_pr_review_action(
    *,
    review_id: str,
    title: str,
    diff_summary: str,
    repo: str,
    pr_number: int | None = None,
    author: str | None = None,
    changed_files: list[str] | None = None,
    extra_context: dict[str, Any] | None = None,
) -> ProposedAction:
    context: dict[str, Any] = {
        "repo": repo,
        "review_kind": "pull_request",
        "changed_files": changed_files or [],
    }
    if pr_number is not None:
        context["pr_number"] = pr_number
    if author is not None:
        context["author"] = author
    if extra_context:
        context.update(extra_context)

    description = f"Review PR change set: {title}\n\nDiff summary:\n{diff_summary}"
    return ProposedAction(
        id=review_id,
        description=description,
        context=context,
        proposed_by=author or "agent",
    )
