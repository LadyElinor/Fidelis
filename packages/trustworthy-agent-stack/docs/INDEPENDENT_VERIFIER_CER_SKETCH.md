# INDEPENDENT_VERIFIER_CER_SKETCH.md

## Purpose

This document sketches CER record types for an independent verifier seam inside TrustworthyAgentStack.

The objective is to ensure that a proposed finding, claim, or safety-relevant observation is not treated as operational truth until a second stage has independently checked it.

## Design principle

A proposer may create a candidate.
A verifier must determine whether the candidate survives reproduction or independent checking.

The stack should primarily act on the verifier-side result.

## Suggested record lifecycle

```text
candidate_find
  -> independent_verification
  -> verification_result
  -> dedupe_decision
  -> patch_grade
  -> reattack_attempt
```

Not every flow needs all record types, but the first three are the core seam.

## 1. `candidate_find`

### Meaning
A first-stage component proposes a finding, issue, concern, or testable claim.

### Suggested payload
```json
{
  "candidate_id": "cand_0001",
  "step_id": "step_001",
  "claim_type": "vulnerability|policy_violation|warrant_disagreement|receipt_anomaly|other",
  "summary": "short human-readable description",
  "evidence_ref": "path_or_record_id",
  "producer": "agent_or_component_name",
  "reproduction_hint": "minimal instructions or artifact reference",
  "created_at": "ISO-8601"
}
```

### Interpretation
This is a candidate, not a confirmed truth.

## 2. `independent_verification`

### Meaning
A verifier stage begins work using the proposer artifact in a clean context.

### Suggested payload
```json
{
  "verification_id": "ver_0001",
  "candidate_id": "cand_0001",
  "step_id": "step_001",
  "verifier": "agent_or_component_name",
  "input_artifact_ref": "candidate_evidence_ref_or_export",
  "verification_mode": "reproduce|review|recompute|replay|other",
  "created_at": "ISO-8601"
}
```

### Interpretation
This records that an independent verification pass actually started, and what evidence it used.

## 3. `verification_result`

### Meaning
The verifier reports the outcome of its check.

### Suggested payload
```json
{
  "verification_result_id": "vres_0001",
  "verification_id": "ver_0001",
  "candidate_id": "cand_0001",
  "step_id": "step_001",
  "result": "confirmed|not_confirmed|inconclusive",
  "confidence": 0.92,
  "artifact_ref": "log_path_or_record_id",
  "summary": "what the verifier observed",
  "created_at": "ISO-8601"
}
```

### Interpretation
This is the first record that should influence stronger downstream action.

## 4. `dedupe_decision`

### Meaning
The stack decides whether a confirmed candidate is genuinely new or duplicates an existing issue.

### Suggested payload
```json
{
  "dedupe_id": "dup_0001",
  "candidate_id": "cand_0001",
  "verification_result_id": "vres_0001",
  "decision": "new|duplicate|related|unknown",
  "matched_record_refs": ["cand_0000"],
  "created_at": "ISO-8601"
}
```

## 5. `patch_grade`

### Meaning
A proposed mitigation or patch is evaluated.

### Suggested payload
```json
{
  "patch_grade_id": "pg_0001",
  "candidate_id": "cand_0001",
  "status": "pass|fail|inconclusive",
  "build_ok": true,
  "tests_ok": true,
  "original_issue_blocked": true,
  "created_at": "ISO-8601"
}
```

## 6. `reattack_attempt`

### Meaning
A fresh attempt is made to rediscover or bypass the fix.

### Suggested payload
```json
{
  "reattack_id": "ra_0001",
  "candidate_id": "cand_0001",
  "patch_grade_id": "pg_0001",
  "result": "blocked|bypassed|inconclusive",
  "summary": "brief description of outcome",
  "created_at": "ISO-8601"
}
```

## Minimal operational rule

A `candidate_find` alone should not justify high-confidence action.

At minimum, stronger action should require:
- `candidate_find`
- `independent_verification`
- `verification_result`

## Relationship to existing stack parts

- **CER** stores the stage artifacts.
- **SOPHRON** validates structure, chronology, and linkage.
- **VITA-M1.1** can evaluate whether the response to the verified claim is warranted.
- **warrant_assay** can analyze whether the council's resulting action is morally justified rather than merely salient.

## Suggested validator invariants

Future SOPHRON rules could require:
- every `verification_result` must reference an existing `independent_verification`
- every `independent_verification` must reference an existing `candidate_find`
- no `verification_result` may precede its `independent_verification`
- no `patch_grade` may exist without a prior `verification_result`
- no `reattack_attempt` may exist without a prior `patch_grade`

## Bottom line

This seam turns independent confirmation into a first-class part of the receipt model.

That is the most valuable architectural import from the reference harness.
