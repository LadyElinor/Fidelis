# CER Next Steps Checklist (v0.1 → usable)

Goal: ship a working, queryable CER telemetry loop (schema → emitter → queries → dashboard/report → community contributions).

## Phase 1 — Freeze v0.1 artifacts (0.5 day)
- [x] **Field freeze**: mark each table field as Required/Optional (no churn)
- [x] **Enum freeze**: gates, decisions, external_action.type/status, confirmation.scope
- [x] **Index freeze**: commit the recommended indexes (SQLite-first)
- [x] **Invariants list**: copy the 3 minimal invariants into a single “MUST” section
- [x] **NULL/bounds semantics**: one paragraph per safety-critical metric explaining lower/upper bound rule
- [x] **Changelog stub**: add a v0.1.1 section (even if empty) for future deltas

Deliverable: v0.1 docs stable enough that others can implement.

## Phase 2 — Reference DB + migrations (0.5–1 day)
- [x] Create `schema.sql` for all v0.1 tables
- [x] Add `migrations/` with versioned SQL (even if minimal)
- [x] Add `indexes.sql` (or bake indexes into schema)
- [x] Add a tiny seed script to create an empty DB
- [x] Add `PRAGMA foreign_keys=ON` note for SQLite

Deliverable: `cer_telemetry.sqlite` can be created from scratch reliably.

## Phase 3 — Minimal emitter library (1 day)
Implement an API that any agent runtime can call:
- [x] `start_run(agent_name, channel, model, config_hash) -> run_id`
- [x] `log_step(run_id, t, event_time, user_text_hash?, assistant_text_hash?) -> step_id`
- [x] `log_gate_check(step_id, gate, decision, justification, confidence?, evidence_ref?)`
- [x] `log_confirmation(step_id, scope, confirmed, created_at)`
- [x] `link_gate_check_confirmation(gate_check_id, confirmation_id)`
- [x] `log_tool_call(step_id, tool, operation, args_hash, outcome, started_at, ended_at?, error_code?)`
- [x] `log_external_action(step_id, type, target, payload_hash, status, created_at, failure_reason?, auth_evidence?)`
- [x] `log_receipt(step_id, receipt_type, fields_present, fields_expected, receipt_json?, created_at)`
- [x] `log_data_issue(run_id, step_id?, kind, severity, details)`

Quality bar:
- [x] O(1) inserts; no JSON parsing required
- [x] Safe-by-default: never store raw secrets; hash payloads

Deliverable: a working, boring emitter.

## Phase 4 — OpenClaw integration (1–2 days)
Minimum wiring (high leverage):
- [x] On session start/end: write `runs`
- [x] On each assistant/user exchange: write `steps` (hash-only)
- [x] On each gate decision: write `gate_checks`
- [x] On each explicit user confirmation: write `confirmations` + linkage
- [x] On each tool call: write `tool_calls`
- [x] On every outbound attempt (even blocked): write `external_actions`
- [x] If something expected is missing: write `data_issues` (don’t hide gaps)

Deliverable: real traces in SQLite from real usage.

## Phase 5 — “Safety CI” query pack (0.5–1 day)
Create `queries/` (SQL) + a small runner script:
- [x] Gate decision rates by gate (pass/warn/escalate/block)
- [x] Safety exception rate per 100 steps
- [x] Exposure attempt/send/block rates
- [x] Confirmation compliance violations (lower + upper bound)
- [x] Confirmation latency (p50/p90/p99) per scope
- [x] Receipt completeness (avg + worst 10 steps)
- [x] Data issues summary (by kind/severity)

Deliverable: one command produces a readable report.

## Phase 6 — Drift monitoring (0.5–1 day)
- [x] Compute per-run aggregates and store in a `run_metrics` view/table
- [x] EWMA for: safety exception rate, exposure_attempt_rate, receipt completeness
- [x] CUSUM / rare-event counter for confirmation compliance violations
- [x] Config diff report: compare config_hash A vs B over windows

Deliverable: regression signals when behavior changes.

## Phase 7 — Shareable export + redaction validation (0.5 day)
- [x] Export script: produce a sanitized DB dump or JSONL bundle
- [x] Validate redaction rules:
  - [x] no raw message bodies
  - [x] no tokens/headers
  - [x] targets are non-sensitive (host/platform)
- [x] Include bounds reporting in exports (avoid metric theater)

Deliverable: safe-to-share traces for community debugging.

## Phase 8 — Community “contribution loop” post (0.25 day)
- [x] Post: “Pick ONE: missing field / invariant / metric contract”
- [x] Provide template:
  - Field: name, table, type, what query it enables
  - Invariant: SQL-checkable statement + why it matters
  - Metric: inputs, NULL policy/bounds, expected complexity
- [x] Link to the three v0.1 artifacts + example query pack

Deliverable: structured feedback instead of vibes.

---

## Suggested 2-day sprint plan
**Day 1**
- Freeze v0.1 artifacts
- Ship schema.sql + migrations
- Draft query pack skeleton

**Day 2**
- Implement emitter + wire into OpenClaw for external_actions + confirmations + gate_checks
- Run on a handful of real sessions
- Generate first Safety CI report

## Definition of done (v0.1 “works”)
- You can answer with SQL:
  - “Did any irreversible action go out without confirmation (bounds)?”
  - “What is exposure attempt rate over the last N runs?”
  - “Did receipt completeness regress after config change?”
- Missing data shows up as `data_issues`, not silent undercount.
