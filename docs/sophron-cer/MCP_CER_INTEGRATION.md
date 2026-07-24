# MCP → CER Integration

This branch’s native architecture is Python + SQLite CER telemetry, not the older JS alignment pipeline.

So MCP support is expressed here as:
- JSONL event ingestion
- step/tool/gate/external-action/receipt emission into CER SQLite
- conservative data-issue logging for risk flags and redaction concerns

## Entry point
- `assistant_tools/assistant_tools/mcp_cer_ingest.py`

## Input model
Each JSONL line is one MCP/runtime event. Useful fields include:
- `event_id`
- `session_id`
- `trace_id`
- `timestamp`
- `tool`
- `operation`
- `input`
- `output`
- `outcome`
- `risk_flags`
- `details`
- `external_action`
- `redacted`
- `redaction_score`
- `session_mismatch`
- `orphan_trace`
- `redaction_unknown`

## Native CER mapping
- event → `steps`
- tool execution → `tool_calls`
- gate/decision hints → `gate_checks`
- outbound attempts → `external_actions`
- MCP action envelope → `receipts`
- leak/risk findings → `data_issues`

## Leak-policy support
Policy overrides support:
- `minimumIndicatorCount`
- `redactionMismatchScore`
- per-pattern enable/disable for:
  - `email-like-content`
  - `key-like-content`
  - `ssn-like-content`
  - `card-like-content`

## Example
```bash
python scripts/seed_cer_telemetry_db.py --db outputs/mcp_fixture.sqlite
python -m assistant_tools.assistant_tools.mcp_cer_ingest assistant_tools/assistant_tools/mcp_mixed_session_fixture.jsonl --db outputs/mcp_fixture.sqlite --model mcp-fixture --leak-policy assistant_tools/assistant_tools/mcp_leak_policy_fixture.json
python scripts/run_cer_safety_ci.py --db outputs/mcp_fixture.sqlite --out outputs/mcp_fixture_report.txt
```

## Intent
This is a re-expression of MCP observability into the existing CER telemetry contract, not a verbatim port of the previous JS artifact writer.
