# TRUSTWORTHYAGENTSTACK_VS_DEFENDING_CODE_REFERENCE_HARNESS.md

## Purpose

This note clarifies the relationship between Anthropic's `defending-code-reference-harness` and `TrustworthyAgentStack`.

The two projects share an anti-handwaving instinct, but they differ at the level of **center of gravity**.
They are best understood as complementary systems rather than direct competitors.

## Core difference

Anthropic's `defending-code-reference-harness` is primarily a **vulnerability discovery and remediation harness**.

`TrustworthyAgentStack` is primarily a **governance, provenance, and routing-verification harness**.

That distinction changes what each system treats as its main object of evaluation, where each system locates trust, and what kind of proof each one seeks.

## Side-by-side comparison

| Dimension | `defending-code-reference-harness` | `TrustworthyAgentStack` |
| --- | --- | --- |
| Primary purpose | Find, verify, report, and patch code vulnerabilities | Make agent behavior observable, gateable, auditable, and regime-aware |
| Main object of evaluation | Source code security bugs | Agent decisions, risk states, receipts, routing, and execution permission |
| Verification model | Runtime proof, reproduction, crash evidence, patch validation | Record proof, deterministic receipts, provenance hashes, validator recomputation |
| Default domain | C/C++ memory vulnerabilities, Docker, ASAN | Agent governance, EthicsCouncil hazard evaluation, MCP-style gates, VITA-M1.1, CER/SOPHRON |
| Agent role | Attack code, produce PoCs, verify crashes, propose patches | Assess risk, block/escalate actions, export receipts, validate evidence chains |
| Safety mechanism | Sandboxing, isolated execution, verifier separation | Invariants, explicit confirmation branch, routing policy, corrective halt behavior |
| Maturity claim | Reference implementation, not maintained, not a product | Runnable minimal proof, explicitly not production infrastructure |

## Philosophical difference

Anthropic's harness asks:

> Can an autonomous agent find a real vulnerability and prove it by reproducing an execution-level failure?

`TrustworthyAgentStack` asks:

> Can an agent's decision path be constrained, recorded, checked, and halted when the risk regime demands it?

Anthropic is therefore more **bug-centric**.
`TrustworthyAgentStack` is more **decision-centric**.

## Different truth sources

The projects answer different kinds of trust questions.

### `defending-code-reference-harness`
Its truth source is primarily **environmental reproduction**.
A claim becomes strong when:
- the target actually fails or crashes
- a separate verifier reproduces that failure
- a mitigation blocks the original issue and survives retesting

### `TrustworthyAgentStack`
Its truth source is primarily **procedural legitimacy**.
A decision becomes strong when:
- risk is classified
- gates are applied
- blocking, review, or confirmation is triggered correctly
- receipts export deterministic structure
- validators recompute and confirm integrity
- invariant violations halt or escalate the flow

## Shared instinct

Despite the difference in center of gravity, both projects share a deep architectural instinct:

**Do not trust model prose. Require artifacts that another process can check.**

Anthropic expresses that through:
- PoCs
- reproductions
- crash signals
- dedupe stages
- patch grading
- re-attack attempts

`TrustworthyAgentStack` expresses it through:
- CER records
- provenance hashes
- signatures
- SOPHRON-style validation
- routing guardrails
- VITA-M1.1 receipts
- corrective halt behavior

Both are anti-"the model said so" systems.

## Most important architectural distinction

Anthropic's harness is an **inner technical loop**:

```text
inspect target -> generate attack -> run target -> reproduce failure -> patch target
```

`TrustworthyAgentStack` is an **outer governance loop**:

```text
evaluate action -> classify risk -> decide whether action may proceed -> record receipt -> validate provenance -> halt or review if needed
```

This is why the systems should be treated as complementary rather than competing.

## Best combined interpretation

A strong integrated architecture would look like:

```text
TrustworthyAgentStack
  governs when and how an autonomous security agent may run
  with what permissions, review obligations, and confirmation requirements

  ↓

Anthropic-style vulnerability harness
  performs sandboxed vulnerability discovery, verification, reporting, and patch attempts

  ↓

TrustworthyAgentStack
  records findings, verifier results, dedupe decisions, patch attempts,
  approvals, rejections, and escalations as CER/SOPHRON-compatible receipts
```

## What `TrustworthyAgentStack` has that the reference harness mostly does not

`TrustworthyAgentStack` has a clearer governance vocabulary for general agent action:
- risk and status classification
- explicit confirmation branches
- corrective halt behavior
- plurality checks
- routing policy helpers
- never-auto-route cases
- adversarial posture around unsafe routing and prompt abuse
- future seams such as `warrant_assay`

## What the reference harness has that `TrustworthyAgentStack` mostly does not

Anthropic's harness has a more concrete domain execution plane:
- real target builds
- sandboxed autonomous execution
- find agents
- independent verifier agents
- exploitability reporting
- patch agents
- patch graders
- reproducible runtime artifacts

`TrustworthyAgentStack` is stronger as a **control plane**.
The reference harness is stronger as a **domain-specific execution plane**.

## Bottom line

`defending-code-reference-harness` is about:

> Can agents safely discover and help fix vulnerabilities in code?

`TrustworthyAgentStack` is about:

> Can agents be made auditable, gateable, reviewable, and unable to silently cross risk boundaries?

The right conclusion is not that one replaces the other.
The right conclusion is that `TrustworthyAgentStack` can serve as the supervisory and evidentiary layer that makes an Anthropic-style execution harness more governable.
