# CER ↔ SOPHRON-CER Export Contract (draft)

Status: proposed / exploratory

## Current implemented export
The Python CER layer now provides an export seam on `CerEmitter`:
- `export_for_sophron(run_id, output_path)`

It emits JSONL records in stable order:
1. `run`
2. `step`
3. `gate_check`
4. `confirmation`
5. `gate_check_confirmation`
6. `tool_call`
7. `external_action`
8. `receipt`
9. `data_issue`

## Envelope
Each JSONL line contains:
- `contract_version`
- `export_timestamp`
- `record_type`
- `schema_version`
- `run_id`
- `provenance_hash`
- `payload`
- `extensions`

## Current contract values
- `contract_version`: `0.1`
- `schema_version`: `0.1`

## Provenance hashing
`provenance_hash` is currently computed as SHA-256 over normalized JSON containing:
- `record_type`
- `run_id`
- `schema_version`
- `payload`

This is an integrity aid, not yet a signature system.

## Scope
This export mirrors the current CER SQLite tables and does not yet add analysis-enriched summaries or live SOPHRON ingestion.
