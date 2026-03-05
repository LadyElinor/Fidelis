from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from assistant_tools.cer_openclaw_integration import OpenClawCerSession
from assistant_tools.prompt_contract_lint import lint_prompt_contract
from assistant_tools.receipt import generate_receipt
from assistant_tools.repo_ingest import ingest_repo
from assistant_tools.safety_gate import run_safety_gates
from assistant_tools.tool_call_log import append_tool_call


def run_workflow_smoke(
    repo_url: str,
    report_dir: str = "logs/smoke",
    safety_config: str = "assistant_tools/configs/safety_gates_example.json",
    log_path: str = "logs/tool_call_log.jsonl",
    cer_db: str | None = "cer_telemetry.sqlite",
) -> dict:
    started = int(time.time())
    out_dir = Path(report_dir) / str(started)
    out_dir.mkdir(parents=True, exist_ok=True)

    steps: list[dict] = []
    cer = OpenClawCerSession(db_path=cer_db, model="assistant_tools.workflow_smoke", config_hash=repo_url) if cer_db else None

    # 1) ingest
    t0 = time.time()
    manifest = ingest_repo(
        repo_url,
        out_root=str(out_dir / "external"),
        include=["README*", "**/*.md", "**/*.txt", "**/*.json"],
        exclude=["**/.git/**", "**/__pycache__/**"],
    )
    ingest_ms = int((time.time() - t0) * 1000)
    append_tool_call(
        log_path=log_path,
        tool="repo_ingest",
        ok=True,
        args={"repo_url": repo_url},
        result={"repo": manifest.get("repo"), "count": manifest.get("count")},
        duration_ms=ingest_ms,
        tags=["smoke", "workflow"],
    )
    ingest_step = {"name": "repo_ingest", "ok": True, "count": manifest.get("count", 0), "duration_ms": ingest_ms}
    steps.append(ingest_step)

    if cer:
        sid = cer.log_exchange(user_text=f"Ingest {repo_url}", assistant_text=json.dumps(ingest_step, sort_keys=True))
        cer.log_tool_call(step_id=sid, tool="repo_ingest", operation="run", args_payload={"repo_url": repo_url}, ok=True, started_at=str(t0), ended_at=str(time.time()))
        cer.log_external_action(step_id=sid, action_type="other", target="github", payload={"repo_url": repo_url}, status="sent")

    # 2) prompt lint (self-contained fixture)
    prompt_text = (
        "Return JSON only between <OUTPUT> and </OUTPUT>.\n"
        "The response must be valid JSON and include all required fields.\n"
        "<OUTPUT>{...}</OUTPUT>\n"
    )
    schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string"},
            "details": {"type": "string"},
        },
        "required": ["status", "details"],
        "additionalProperties": False,
    }

    t1 = time.time()
    lint_issues = lint_prompt_contract(prompt_text, schema)
    lint_ok = len(lint_issues) == 0
    lint_ms = int((time.time() - t1) * 1000)
    append_tool_call(
        log_path=log_path,
        tool="prompt_contract_lint",
        ok=lint_ok,
        args={"fixture": True},
        result={"issues": lint_issues},
        duration_ms=lint_ms,
        tags=["smoke", "workflow"],
    )
    lint_step = {"name": "prompt_contract_lint", "ok": lint_ok, "issues": lint_issues, "duration_ms": lint_ms}
    steps.append(lint_step)

    if cer:
        sid = cer.log_exchange(user_text="Run prompt contract lint", assistant_text=json.dumps(lint_step, sort_keys=True))
        cer.log_tool_call(step_id=sid, tool="prompt_contract_lint", operation="run", args_payload={"fixture": True}, ok=lint_ok, started_at=str(t1), ended_at=str(time.time()), error_code=None if lint_ok else "lint_issues")
        if not lint_ok:
            cer.log_data_issue(kind="other", severity="warn", details="prompt_contract_lint produced issues", step_id=sid)

    # 3) safety gate
    t2 = time.time()
    safety_report_path = out_dir / "safety_report.json"
    safety_report = run_safety_gates(safety_config, report_path=str(safety_report_path))
    safety_ms = int((time.time() - t2) * 1000)
    append_tool_call(
        log_path=log_path,
        tool="safety_gate",
        ok=bool(safety_report.get("ok")),
        args={"config": safety_config},
        result={"ran": len(safety_report.get("results", []))},
        duration_ms=safety_ms,
        tags=["smoke", "workflow"],
    )
    safety_step = {
        "name": "safety_gate",
        "ok": bool(safety_report.get("ok")),
        "ran": len(safety_report.get("results", [])),
        "duration_ms": safety_ms,
        "report": str(safety_report_path).replace("\\", "/"),
    }
    steps.append(safety_step)

    if cer:
        sid = cer.log_exchange(user_text="Run safety gates", assistant_text=json.dumps(safety_step, sort_keys=True))
        cer.log_tool_call(step_id=sid, tool="safety_gate", operation="run", args_payload={"config": safety_config}, ok=bool(safety_report.get("ok")), started_at=str(t2), ended_at=str(time.time()))
        gate_decision = "pass" if safety_report.get("ok") else "block"
        gate_check_id = cer.log_gate(step_id=sid, gate="traceability", decision=gate_decision, justification="assistant_tools safety gate aggregate")
        conf_id = cer.log_confirmation(step_id=sid, scope="external_action", confirmed=bool(safety_report.get("ok")))
        cer._emitter.link_gate_check_confirmation(gate_check_id, conf_id)

    # 4) receipt
    t3 = time.time()
    receipt_txt = generate_receipt(
        title="assistant_tools workflow smoke",
        notes=(
            f"repo={manifest.get('repo')} count={manifest.get('count')}\n"
            f"lint_ok={lint_ok} issues={len(lint_issues)}\n"
            f"safety_ok={safety_report.get('ok')}"
        ),
        include_git=False,
    )
    receipt_path = out_dir / "receipt.txt"
    receipt_path.write_text(receipt_txt, encoding="utf-8")
    receipt_ms = int((time.time() - t3) * 1000)
    append_tool_call(
        log_path=log_path,
        tool="receipt",
        ok=True,
        args={"title": "assistant_tools workflow smoke"},
        result={"path": str(receipt_path).replace('\\', '/')},
        duration_ms=receipt_ms,
        tags=["smoke", "workflow"],
    )
    receipt_step = {"name": "receipt", "ok": True, "duration_ms": receipt_ms, "path": str(receipt_path).replace("\\", "/")}
    steps.append(receipt_step)

    if cer:
        sid = cer.log_exchange(user_text="Generate receipt", assistant_text=json.dumps(receipt_step, sort_keys=True))
        cer.log_tool_call(step_id=sid, tool="receipt", operation="run", args_payload={"title": "assistant_tools workflow smoke"}, ok=True, started_at=str(t3), ended_at=str(time.time()))
        cer.log_receipt(step_id=sid, receipt_type="summary", fields_present=3, fields_expected=3, receipt_payload={"path": str(receipt_path).replace('\\', '/')})

    overall_ok = all(step.get("ok") for step in steps)
    summary = {
        "ok": overall_ok,
        "started_unix": started,
        "repo_url": repo_url,
        "output_dir": str(out_dir).replace("\\", "/"),
        "steps": steps,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if cer:
        cer.close()
    return summary


def cmd_workflow_smoke(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("workflow_smoke", help="Run end-to-end smoke: ingest -> lint -> safety_gate -> receipt/log")
    p.add_argument("--repo-url", default="https://github.com/octocat/Hello-World")
    p.add_argument("--report-dir", default="logs/smoke")
    p.add_argument("--safety-config", default="assistant_tools/configs/safety_gates_example.json")
    p.add_argument("--log", default="logs/tool_call_log.jsonl")
    p.add_argument("--cer-db", default="cer_telemetry.sqlite")

    def _run(args: argparse.Namespace) -> int:
        summary = run_workflow_smoke(
            repo_url=args.repo_url,
            report_dir=args.report_dir,
            safety_config=args.safety_config,
            log_path=args.log,
            cer_db=args.cer_db,
        )
        print(json.dumps({"ok": summary["ok"], "output_dir": summary["output_dir"]}, indent=2))
        return 0 if summary["ok"] else 1

    p.set_defaults(_run=_run)
