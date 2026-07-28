from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from trusted_runtime.action_identity import legacy_approval_target_shim
from trusted_runtime.export import export_decision_payload
from trusted_runtime.integration.engine import assemble_execution_decision
from trusted_runtime.integration.report import render_markdown_report
from trusted_runtime.shared.models import ExactApprovalTarget, ProposedAction


def _typed_approval_fields_from_context(context: dict[str, Any]) -> tuple[str | None, str | None, ExactApprovalTarget | None]:
    """Lift legacy context-based approval shaping into the preferred typed surface."""
    action_scope = context.get("action_scope") if isinstance(context.get("action_scope"), str) else None
    source_digest = context.get("source_digest") if isinstance(context.get("source_digest"), str) else None
    shim_action = ProposedAction(id="legacy-context-shim", description="legacy-context-shim", context=context)
    target_connector, target_destination, target_arguments = legacy_approval_target_shim(shim_action)
    exact_approval_target = None
    if target_connector is not None or target_destination is not None or target_arguments is not None:
        exact_approval_target = ExactApprovalTarget(
            connector=target_connector,
            destination=target_destination,
            arguments=target_arguments,
        )
    return action_scope, source_digest, exact_approval_target


def load_review_input(path: Path) -> ProposedAction:
    payload = json.loads(path.read_text(encoding="utf-8"))
    action = ProposedAction.model_validate(payload)
    if action.action_scope is None and action.source_digest is None and action.exact_approval_target is None:
        action_scope, source_digest, exact_approval_target = _typed_approval_fields_from_context(action.context)
        if action_scope is not None or source_digest is not None or exact_approval_target is not None:
            action = action.model_copy(
                update={
                    "action_scope": action_scope,
                    "source_digest": source_digest,
                    "exact_approval_target": exact_approval_target,
                    "typed_approval_lifted_from_legacy": True,
                }
            )
    return action


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
        "action_scope": "state_change" if changed_files else "general",
    }
    if pr_number is not None:
        context["pr_number"] = pr_number
    if author is not None:
        context["author"] = author
    if extra_context:
        context.update(extra_context)

    action_scope, source_digest, exact_approval_target = _typed_approval_fields_from_context(context)

    description = f"Review PR change set: {title}\n\nDiff summary:\n{diff_summary}"
    return ProposedAction(
        id=review_id,
        description=description,
        context=context,
        proposed_by=author or "agent",
        action_scope=action_scope,
        review_kind=context.get("review_kind") if isinstance(context.get("review_kind"), str) else None,
        change_type=context.get("change_type") if isinstance(context.get("change_type"), str) else None,
        changed_files=context.get("changed_files") if isinstance(context.get("changed_files"), list) else None,
        source_digest=source_digest,
        exact_approval_target=exact_approval_target,
        typed_approval_lifted_from_legacy=False,
    )
