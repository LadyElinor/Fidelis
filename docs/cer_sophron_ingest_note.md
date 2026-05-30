# CER export ingest note

This bridge is intentionally minimal.

Current scope:
- ingest CER JSONL export records
- summarize record counts and record types
- surface `data_issue.details` as simple risk flags
- write a small artifact bundle for downstream review

Current artifacts written:
- `meta.json`
- `records.json`
- `summary.json`

This proves CER to SOPHRON handoff, but it is not yet a full semantic mapper into richer SOPHRON-native analytical structures.
