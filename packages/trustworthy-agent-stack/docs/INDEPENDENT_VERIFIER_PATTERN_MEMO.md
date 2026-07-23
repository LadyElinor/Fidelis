# INDEPENDENT_VERIFIER_PATTERN_MEMO.md

## Purpose

This note captures the most useful architectural patterns to import from Anthropic's `defending-code-reference-harness` into TrustworthyAgentStack.

The goal is **not** to copy the whole harness.
The goal is to import the strongest epistemic and safety seams into an invariants-first receipt stack.

## Core judgment

Treat `defending-code-reference-harness` as a **pattern donor** rather than a dependency.

What is valuable is not the specific prompts or C/C++-oriented autonomous flow.
What is valuable is the structure:
- proposer/verifier separation
- runtime-enforced sandboxing
- stage-specific artifacts
- evidence/judgment separation
- regression and re-attack validation

## Patterns worth importing

### 1. Proposer / verifier separation

A first component proposes a finding.
A second component verifies it independently.
Only the minimal evidence required for reproduction crosses the seam.

Why this matters:
- reduces persuasive hallucination
- makes artifacts more trustworthy
- prevents a single reasoning trace from grading itself
- fits naturally into CER + SOPHRON

### 2. Runtime-enforced safety boundaries

Important constraints should live in code and infrastructure:
- sandboxing
- network policy
- file system scope
- permission boundaries
- tool availability

Do not rely on prompt text alone to keep an autonomous or semi-autonomous agent safe.

### 3. Stage-specific records

Separate records should exist for distinct lifecycle stages.
Examples:
- candidate detection
- independent verification
- dedupe judgment
- report generation
- patch grading
- re-attack attempt

Why this matters:
- evidence stays separable from interpretation
- downstream validation can reason locally about each stage
- partial trust is possible without accepting the whole narrative

### 4. Evidence vs judgment separation

A reproduced event is evidence.
A vulnerability classification, warrant judgment, or severity claim is an interpretation layered on top.

TrustworthyAgentStack should preserve this split explicitly:
- observations and receipts
- warrant or hazard interpretation
- deployment-specific decision

### 5. Regression and re-attack validation

After a fix or a blocking action, the system should verify:
- the original issue no longer reproduces
- a fresh attempt does not trivially bypass the mitigation

This is stronger than merely checking that a patch builds or tests pass.

## What not to import wholesale

### 1. The full autonomous harness

Reasons:
- upstream is not maintained
- default scope is narrow
- operational assumptions are specific
- maintenance burden is real

### 2. Product framing

Do not model TrustworthyAgentStack on the assumption that a research harness is a stable scanner or enterprise platform.

### 3. Prompt-specific implementation details

The architecture is more portable than the prompts.
Import structure first, not wording.

## Best concrete transplant into TrustworthyAgentStack

The highest-value import is:

**an independent verifier seam as a first-class CER lifecycle**

This can be generalized beyond vulnerability research.
Any meaningful claim can benefit from:
- proposal
- independent verification
- reconciliation
- durable receipt

## Recommended CER record types

TrustworthyAgentStack should consider introducing dedicated record types such as:
- `candidate_find`
- `independent_verification`
- `verification_result`
- `dedupe_decision`
- `patch_grade`
- `reattack_attempt`

These should remain small, structured, and verifiable.

## Integration rule

Do not let the proposer stage justify itself.

At minimum:
- proposer emits evidence artifact
- verifier consumes that artifact in a clean context
- verifier emits its own receipt
- downstream logic acts primarily on the verifier result, not on the original claim alone

## Bottom line

The strongest import from `defending-code-reference-harness` is not autonomy.
It is **independent confirmation as architecture**.

That principle aligns tightly with:
- CER
- SOPHRON
- VITA-M1.1
- warrant_assay
- evidence-first governance

TrustworthyAgentStack should import that seam deliberately and minimally.
