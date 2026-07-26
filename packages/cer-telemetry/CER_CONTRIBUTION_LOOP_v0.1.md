# CER Telemetry v0.1 — Contribution Loop Call

Pick **ONE** contribution type so feedback stays SQL-checkable and actionable.

## 1) Missing field
- **Field name**:
- **Table**:
- **Type**:
- **Required/Optional**:
- **What query this enables**:
- **Why existing fields are insufficient**:

## 2) Invariant
- **Invariant (SQL-checkable statement)**:
- **Why it matters**:
- **Failure mode if violated**:
- **Suggested detection query**:

## 3) Metric contract
- **Metric name**:
- **Inputs (tables/fields)**:
- **NULL policy + lower/upper bounds**:
- **Expected complexity**:
- **Regression signal meaning**:

## Canonical v0.1 artifacts
- `CER_TELEMETRY_SPEC_v0.1.md`
- `CER_TELEMETRY_IMPLEMENTATION_v0.1.md`
- `CER_TELEMETRY_METRICS_v0.1.md`
- Query pack examples: `queries/`

## Posting template (copy/paste)
```markdown
### CER v0.1 contribution
Type: <field | invariant | metric>

<fill selected section>

Example SQL / pseudocode:
```sql
-- your check/query here
```

Expected impact:
- ...
```
