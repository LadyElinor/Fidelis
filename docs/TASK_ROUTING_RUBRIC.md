# TASK_ROUTING_RUBRIC.md

## Purpose

This rubric decides when a task should be routed to **Picobot**, when it should stay in **OpenClaw**, and when it should **never be auto-routed at all**.

The goal is not maximum automation. The goal is the best balance of:
- quality
- cost
- verification
- context retention
- operational safety

> Prefer losing a little efficiency over losing verification, context, or judgment.

---

## Decision rule

Route to the **smallest system that can complete the task well without materially increasing risk**.

If a task is:
- cheap
- narrow
- low-risk
- low-context
- easy to verify

prefer **Picobot**.

If a task involves:
- ambiguity
- synthesis
- high consequence
- deep context
- governance
- repo surgery
- multi-step verification

prefer **OpenClaw**.

If uncertain, **route upward to OpenClaw**.

---

## Route to Picobot

Use Picobot when the task is structurally simple and the cost savings are real.

Typical Picobot tasks:
- simple reminders
- heartbeat-style checks
- basic Telegram bot interactions
- narrow file reads/writes
- simple note capture
- lightweight web fetches
- routine status checks
- repetitive low-risk personal automation
- small utility workflows on constrained hardware

Picobot is the better choice when all of the following are true:
- task scope is narrow
- failure is low-cost and reversible
- little prior context is needed
- no complex orchestration is required
- the output can be checked quickly

---

## Route to OpenClaw

Use OpenClaw when the task depends on richer context, stronger tooling, or tighter verification discipline.

Typical OpenClaw tasks:
- multi-step research
- repo refactors or code surgery
- cross-project synthesis
- memory-heavy assistant work
- contract design and architecture decisions
- governance or safety reasoning
- subagent orchestration
- artifact-heavy handoff work
- investigations where evidence separation matters
- anything needing careful validation before completion claims

OpenClaw is the better choice when any of the following are true:
- the task is ambiguous
- the task may sprawl
- the task affects multiple systems or repos
- the task has external or public consequence
- the task needs deeper memory continuity
- the task requires stronger proof before reporting success

---

## Never auto-route

These tasks should not be auto-routed to Picobot by default, and often should not be auto-routed anywhere without explicit review.

Examples:
- destructive actions with meaningful downside
- public posting or messaging on behalf of a human
- security-sensitive operations
- secret handling or credential rotation
- governance-critical decisions
- deployment changes with unclear blast radius
- legal, ethical, or compliance-sensitive judgments
- anything with unclear ownership or authorization

These require either:
- explicit human approval
- OpenClaw oversight
- or both

---

## Escalate from Picobot to OpenClaw when

A task begins in Picobot but should be escalated if any of these appear:
- the task is no longer simple
- required context exceeds the local prompt budget
- multiple files/repos/systems become involved
- output confidence drops
- the user asks for explanation, comparison, or synthesis
- verification becomes nontrivial
- the task touches governance, policy, or safety decisions
- the task may trigger external side effects beyond the original scope
- the result cannot be cleanly validated with a short local check

Escalation rule:
- when complexity or consequence rises, route upward early rather than after partial damage

---

## Example classifications

### Route to Picobot
- "Remind me in 20 minutes to check the laundry"
- "Watch this Telegram channel and tell me if my bot gets a message"
- "Fetch this URL every hour and alert me if the status changes"
- "Append this note to today’s log"
- "Check whether this process is still running"

### Route to OpenClaw
- "Compare these three repos and propose an integration plan"
- "Refactor this subsystem and preserve behavior"
- "Investigate why this telemetry contract keeps drifting"
- "Review this architecture and identify weak assumptions"
- "Summarize the state of this project family from code and docs"

### Never auto-route without review
- "Push changes to production"
- "Message this person for me"
- "Rotate these credentials"
- "Delete this dataset"
- "Approve this governance or policy exception"

---

## Default bias when uncertain

Use this tie-break rule:

- if cheap, small, simple, and low-risk, prefer **Picobot**
- if ambiguity, synthesis, repo surgery, governance, or public/external consequence is present, prefer **OpenClaw**
- if unsure, **route upward to OpenClaw**

OpenClaw is the default escalator.
Picobot is the cost-efficient satellite.

That is the intended relationship.
