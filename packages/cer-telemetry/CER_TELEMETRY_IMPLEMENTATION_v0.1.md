# CER Telemetry Implementation Contract (v0.1)

This file freezes the operational contract for implementers.

## SQLite note
- Always enable: `PRAGMA foreign_keys = ON;`

## Field freeze (Required/Optional)

### runs
- Required: `run_id`, `started_at`, `agent_name`, `channel`, `model`, `config_hash`
- Optional: `ended_at`

### steps
- Required: `step_id`, `run_id`, `t`, `event_time`
- Optional: `user_text_hash`, `assistant_text_hash`

### gate_checks
- Required: `gate_check_id`, `step_id`, `gate`, `decision`, `justification`, `created_at`
- Optional: `confidence`, `evidence_ref`

### confirmations
- Required: `confirmation_id`, `step_id`, `scope`, `confirmed`, `created_at`
- Optional: none

### gate_check_confirmations
- Required: `gate_check_id`, `confirmation_id`
- Optional: none

### tool_calls
- Required: `tool_call_id`, `step_id`, `tool`, `operation`, `args_hash`, `outcome`, `started_at`
- Optional: `ended_at`, `error_code`

### external_actions
- Required: `external_action_id`, `step_id`, `type`, `target`, `payload_hash`, `status`, `created_at`
- Optional: `failure_reason`, `auth_evidence`

### receipts
- Required: `receipt_id`, `step_id`, `receipt_type`, `fields_present`, `fields_expected`, `created_at`
- Optional: `receipt_json`

### data_issues
- Required: `issue_id`, `run_id`, `kind`, `severity`, `details`, `created_at`
- Optional: `step_id`

## Enum freeze
- `gate`: `intent|authority|irreversibility|exposure|traceability`
- `decision`: `pass|warn|escalate|block`
- `external_actions.type`: `post|reply|dm|email|purchase|delete|upload|other`
- `external_actions.status`: `attempted|blocked|sent|failed`
- `confirmations.scope`: `external_action|message_send|deletion|purchase|credential_change|other`

## Index freeze (SQLite-first)
- `steps(run_id, t)`
- `gate_checks(gate, decision)`
- `gate_checks(step_id)`
- `external_actions(status, type)`
- `external_actions(step_id)`
- `external_actions(target)`
- `confirmations(scope, confirmed)`
- `confirmations(step_id)`

## MUST invariants (single list)
1. No irreversible sent action without confirmation evidence (lower/upper bounds reported).
2. Every outbound attempt is explicitly represented in `external_actions`, including blocked attempts.
3. Receipt completeness is measurable per step/run via `fields_present / fields_expected`.

## NULL / bounds semantics for safety-critical metrics

### Confirmation compliance
- Lower bound: only provable violations (`sent` irreversible action with no confirmed evidence).
- Upper bound: lower-bound violations plus any rows where evidence is missing/unknown.

### Exposure attempt/send/block rates
- Include all `external_actions` rows; do not infer missing attempts from tool logs.
- If evidence is missing, add `data_issues` and treat unknowns conservatively in upper-bound reporting.

### Receipt completeness
- Use `fields_present / max(fields_expected, 1)`.
- Missing receipt rows are counted as unknown and should be surfaced through `data_issues`.

## Changelog
### v0.1.1 (stub)
- (no changes yet)
