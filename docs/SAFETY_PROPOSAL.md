# Proposal for advancing safety in Fidelis

## Executive summary

Fidelis already establishes a strong foundation for trustworthy agent operation through explicit authority, independent ethical evaluation, warrant assessment, receipt generation, and fail-closed execution. Its central safety insight is sound: no component should be able to create, expand, or certify its own authority merely by producing convincing output.

The next stage of development should extend these principles from deliberation into the entire operational path between human intent and external action.

The principal safety objective should be:

> No data, model output, retrieved instruction, prior approval, or compromised component may cause a consequential action unless the exact action is supported by current, authenticated, narrowly scoped, and independently verifiable authority.

This proposal recommends a four-part safety program:

1. repair and formalize the authority model;
2. bind human approval to exact, single-use actions;
3. isolate untrusted content from executable intent;
4. make side effects transactional, auditable, and resistant to replay, concurrency, and state changes.

The result would be a runtime that does more than evaluate whether an action appears ethical. It would establish whether the action is authorized, whether the supporting state is still current, whether the proposed data flow matches the approval, and whether the execution can be independently reconstructed afterward.

## 1. Safety goals

Fidelis should be designed to satisfy the following invariants.

### 1.1 Authority cannot be self-created

An agent, evaluator, tool, retrieved document, or subordinate component may propose an action, supply evidence, or identify a risk. None may grant itself permission to act.

### 1.2 Data cannot silently become instruction

Content retrieved from a repository, webpage, email, document, tool result, or memory must remain data unless an authenticated operator explicitly adopts it as an instruction.

### 1.3 Approval applies only to the exact approved act

Approval for one recipient, file, command, connector, account, amount, or destination must not authorize a modified action.

### 1.4 Revoked authority cannot survive through delegation

When a parent grant is revoked or expires, every dependent delegation must immediately become unusable unless supported by an independent valid authority path.

### 1.5 Receipts must identify what they prove

A receipt may prove that a component emitted a result, that a policy was evaluated, or that an action was executed. It must not imply that the underlying judgment was correct unless a separate verification supports that claim.

### 1.6 Safety must apply to cumulative conduct

A harmful operation must not become permissible merely because it is decomposed into individually innocuous steps.

### 1.7 State changes invalidate stale approval

If a document, branch, recipient list, account, policy, authority state, or execution target changes after approval, the runtime must suspend the action and require reevaluation.

### 1.8 Side effects must fail closed

When authority, policy, provenance, durable state, or verification is unavailable, Fidelis must preserve the proposed action as a suspended artifact rather than execute it.

## 2. Current safety strengths

Fidelis should preserve and deepen its existing architectural commitments:

- independent ethical lenses rather than a single moral classifier;
- separate significance and warrant evaluation;
- explicit authority resolution;
- typed claims and provenance;
- receipt chains;
- non-self-certifying components;
- a thin runtime that delegates judgments without surrendering control;
- side effects disabled unless required validations are real;
- visible suspension rather than silent fallback.

These elements make Fidelis well suited to becoming a reference architecture for bounded agent execution. The main work now is to ensure that these protections remain intact across delegation, tool use, external data, retries, concurrent processes, and runtime recovery.

## 3. Proposed safety architecture

The recommended architecture introduces seven linked controls.

### 3.1 Trust-typed inputs

Every value entering the runtime should carry an immutable trust classification.

A minimum trust envelope should include:

```python
class TrustEnvelope:
    value: object
    origin_class: str
    origin_reference: str
    content_digest: str
    authenticated_principal: str | None
    may_supply_facts: bool
    may_supply_instructions: bool
    may_grant_authority: bool
```

Suggested origin classes include:

- authenticated current operator;
- runtime policy;
- agent proposal;
- retrieved content;
- tool output;
- external message;
- memory;
- imported configuration;
- system-generated state.

Default behavior should be restrictive.

Retrieved content may normally provide facts but not commands. Agent output may propose actions but not authorize them. Memory may provide context but not new permission. Tool output may describe the environment but must not alter policy or authority.

Trust metadata must survive transformations. Summarizing a malicious document must not convert its embedded instructions into operator intent.

### 3.2 Typed action objects

The current concept of a proposed action should become a closed, discriminated set of action types.

Examples include:

- `ReadAction`
- `WriteAction`
- `SendAction`
- `ExecuteAction`
- `DeleteAction`
- `PublishAction`
- `TransferAction`
- `AuthorityChangeAction`

Every action should specify:

- actor;
- action class;
- tool or connector;
- target;
- full normalized arguments;
- source objects;
- destination;
- affected principals;
- expected state before execution;
- expected state after execution;
- reversibility;
- required authority scope;
- data-egress manifest;
- risk classification;
- intent identifier;
- idempotency key.

Unknown fields should be rejected rather than passed through as unexamined context.

Typed actions allow safety rules to operate on actual semantics. A `SendAction`, for example, can require a recipient, message digest, attachment list, egress declaration, and connector identity. An `AuthorityChangeAction` can require stronger approval and dual control.

### 3.3 Action-bound approval capabilities

Human approval should be represented as a narrow capability rather than a durable general-purpose grant.

An approval capability should bind to:

- exact action digest;
- normalized arguments;
- connector identity;
- account identity;
- destination;
- recipient;
- source-object digests;
- data-egress manifest;
- policy snapshot;
- authority-state snapshot;
- approval time;
- expiration time;
- authenticated approver;
- unique nonce;
- single-use status.

A change to any bound field must invalidate the approval.

For consequential actions, broad approval scopes such as general should not be sufficient. Broad grants may authorize evaluation or preparation, but the final external side effect should require a specific approval capability.

This creates a clear distinction between:

- permission to prepare an email;
- permission to send this exact email, with these attachments, through this account, to this recipient.

The executor should atomically consume the approval nonce. Retries must use an idempotency protocol rather than reusing approval indefinitely.

### 3.4 Transitive authority validation

Delegated authority must remain valid only while its entire ancestry remains valid.

At resolution time, Fidelis should verify:

```text
grant exists
AND grant is active
AND grant is not expired
AND grant is not revoked
AND parent remains valid
AND every ancestor remains valid
AND scope remains within every ancestor's scope
AND effective strength does not exceed the weakest ancestor
```

A child grant must immediately fail if its parent is revoked, expired, removed, or rendered invalid by a policy change.

Recommended resolution states include:

- valid;
- expired;
- revoked;
- ancestor expired;
- ancestor revoked;
- parent missing;
- scope violation;
- strength violation;
- chain malformed;
- journal unverifiable.

A reverse dependency index should identify affected descendants for diagnostics and efficient invalidation. Correctness, however, should come from live chain validation rather than cached propagation alone.

### 3.5 Data-egress control

Any action that transmits information outside the current trust boundary should carry a structured egress manifest.

The manifest should state:

- destination;
- provider;
- account;
- fields leaving the system;
- originating resources;
- sensitivity categories;
- transformations applied;
- purpose;
- expected retention;
- applicable approval;
- policy basis.

The final payload should be constructed from approved fields. The runtime should not accept an opaque agent-generated payload and attempt to determine afterward whether it contains prohibited information.

This control should cover:

- email;
- messaging;
- cloud storage;
- web requests;
- repository pushes;
- telemetry;
- model-provider calls;
- file uploads;
- database writes;
- clipboard or local interprocess transfer.

Connector installation or availability must not imply authorization. Approval to perform an operation and approval to disclose data to a particular provider should remain separate decisions.

### 3.6 Cumulative intent and risk ledger

Every related sequence of actions should share an immutable `intent_id`.

The runtime should track the cumulative effect of the sequence, including:

- resources accessed;
- sensitive data accumulated;
- transformations performed;
- destinations contacted;
- permissions acquired;
- irreversible effects;
- external disclosures;
- prior denials or suspensions;
- authority already consumed.

The gate should evaluate not only the current step but also the complete operational trajectory.

For example, the following actions should be considered together:

1. read a credential file;
2. transform its contents;
3. resolve an external endpoint;
4. construct a request body;
5. send the request.

Even when each step is independently described as benign, their combined effect is credential exfiltration.

Starting a new agent session, changing tools, retrying after denial, or splitting work across components must not reset cumulative-risk state.

### 3.7 Transactional side-effect executor

The executor should be a narrow trusted component that accepts only fully authorized action objects.

The execution sequence should be:

```text
1. verify action schema
2. verify trust provenance
3. resolve live authority chain
4. verify approval capability
5. verify policy snapshot
6. verify source and target versions
7. verify cumulative-risk state
8. verify egress manifest
9. reserve idempotency key
10. execute through the named adapter
11. capture outcome
12. commit the receipt
13. consume the approval capability
```

Where possible, the system should reserve execution and approval consumption atomically.

If execution status is uncertain because of a timeout or crash, Fidelis should enter an `UNKNOWN_EXTERNAL_STATE` condition. It must not automatically retry a consequential action until the external system is checked.

## 4. Journal and receipt hardening

### 4.1 Authenticated journal anchors

A hash-linked journal detects changes only when its trusted head is preserved. An attacker able to rewrite the full journal can otherwise recompute the chain.

Fidelis should therefore anchor journal integrity through one or more of the following:

- digital signatures;
- keyed message authentication codes held outside the runtime;
- append-only external storage;
- periodic transparency checkpoints;
- hardware-backed keys;
- replicated independent witnesses.

Receipts should identify:

- journal sequence;
- prior head;
- new head;
- signature;
- signer;
- checkpoint reference;
- resolver semantic version.

### 4.2 Concurrency control

Journal writes should use a single-writer, lock, or compare-and-swap protocol.

A safe append should:

1. acquire exclusive write authority;
2. reread the current head;
3. compare it with the expected head;
4. assign a monotonic sequence number;
5. write a fully framed entry;
6. flush the entry;
7. durably synchronize storage;
8. release the lock.

Concurrent writers must not be able to append two entries that claim the same predecessor without detection.

### 4.3 Semantic state digests

A resolver digest should cover more than active grant identifiers.

It should include:

- active grants;
- journal head;
- evaluation time;
- scope algebra version;
- authority-strength lattice;
- namespace normalization rules;
- policy profile;
- resolver build or release;
- delegation semantics.

Separate digests should be used for separate claims:

- `authority_state_digest`
- `resolver_semantics_digest`
- `policy_digest`
- `journal_head_digest`
- `action_digest`

This prevents a receipt from implying that resolver behavior was unchanged when only the grant list remained constant.

## 5. Prompt-injection and untrusted-content defense

Fidelis should adopt a strict rule:

> Retrieved content can influence factual assessment, but it cannot directly provide executable authority.

The runtime should test against documents, webpages, emails, repository files, and tool results containing statements such as:

- ignore previous instructions;
- treat this block as system policy;
- upload local files;
- reveal credentials;
- create an authority grant;
- mark the action approved;
- execute the following command;
- contact an external destination.

Such content should remain visible as evidence and may be surfaced to the operator. It must not alter the control plane.

The system should also distinguish quoted instructions from adopted instructions. A user asking Fidelis to analyze a malicious prompt is not authorizing Fidelis to follow the prompt.

## 6. Implementation roadmap

### Phase 1: authority correctness

Deliverables:

- recursive delegation-chain validation;
- descendant invalidation after parent revocation;
- explicit authority-resolution failure states;
- canonical authority identifiers;
- authenticated insertion principals;
- separation of authority state and resolver semantics digests.

Exit criteria:

- all transitive revocation tests pass;
- no delegated grant resolves when any required ancestor is invalid;
- semantic changes alter the corresponding resolver digest;
- malformed or ambiguous authority identifiers fail closed.

### Phase 2: exact approval

Deliverables:

- typed action objects;
- deterministic action canonicalization;
- action digests;
- expiring single-use approval capabilities;
- idempotency keys;
- approval mutation detection;
- state-version binding.

Exit criteria:

The executor rejects an approved action when any of the following changes:

- recipient;
- destination;
- account;
- tool;
- argument;
- source digest;
- attachment;
- policy;
- authority state;
- egress manifest.

An approval nonce cannot be successfully consumed twice.

### Phase 3: untrusted content and egress

Deliverables:

- trust envelopes;
- provenance-preserving transformations;
- content-versus-instruction enforcement;
- structured egress manifests;
- connector-specific authorization;
- approved-field payload construction;
- prompt-injection adversarial suite.

Exit criteria:

- retrieved content cannot generate authority;
- tool output cannot masquerade as operator intent;
- unapproved fields cannot cross an external boundary;
- connector substitution invalidates approval;
- quoted malicious instructions remain inert.

### Phase 4: transactional execution

Deliverables:

- narrow side-effect executor;
- compare-and-swap journal writes;
- durable execution records;
- unknown-external-state handling;
- crash recovery;
- external journal anchoring;
- cumulative intent ledger.

Exit criteria:

- concurrent writers cannot fork the journal undetected;
- crashes do not silently duplicate consequential actions;
- ambiguous external outcomes suspend retries;
- multi-step harmful behavior is detected across component and session boundaries.

### Phase 5: independent assurance

Deliverables:

- formal threat model;
- security invariants document;
- property-based tests;
- fault-injection suite;
- red-team corpus;
- independent verifier;
- reproducible safety benchmark;
- public claim ledger.

Exit criteria:

Every public safety claim maps to:

- a defined invariant;
- an implementation control;
- a test;
- a receipt or benchmark;
- a known limitation.

No safety claim should depend solely on the component whose behavior the claim describes.

## 7. Priority test suite

The following tests should be treated as release-blocking.

### Authority

- child invalid after parent revocation;
- grandchild invalid after root expiry;
- delegation cannot exceed parent scope;
- delegation cannot exceed parent strength;
- missing ancestor fails closed;
- future-dated revocation uses evaluation time correctly.

### Approval

- changed recipient invalidates approval;
- changed connector invalidates approval;
- changed argument invalidates approval;
- changed source digest invalidates approval;
- expired approval fails;
- approval nonce is single use;
- broad approval cannot authorize a consequential side effect.

### Injection

- file instruction cannot become user intent;
- tool output cannot create authority;
- forged system marker remains data;
- prior assistant proposal is not user approval;
- memory cannot supply new authority;
- quoted malicious instructions remain inert.

### Egress

- unapproved field cannot reach adapter;
- unapproved attachment cannot be sent;
- provider substitution fails;
- destination mutation fails;
- sensitive data requires declared manifest;
- payload is constructed from approved fields only.

### State and execution

- stale source state requires reapproval;
- concurrent journal writers cannot create an accepted fork;
- rewritten journal fails anchor verification;
- uncertain external outcome prevents blind retry;
- same idempotency key cannot produce duplicate execution.

### Cumulative conduct

- multi-step data exfiltration is detected;
- risk state survives agent handoff;
- risk state survives session restart;
- denied intent cannot be reset by paraphrasing;
- subtasks inherit the parent `intent_id`.

## 8. Governance and development discipline

Safety-critical code should be developed under stricter rules than ordinary feature code.

Recommended controls include:

- mandatory review by a maintainer other than the author;
- branch protection;
- signed releases;
- reproducible builds;
- security-focused change templates;
- invariant impact statements;
- no silent relaxation of fail-closed behavior;
- explicit migration plans for authority data;
- compatibility tests for receipts and journals;
- documented emergency-recovery procedures;
- separation between root-authority maintainers and ordinary component maintainers.

Changes to the following areas should require elevated review:

- authority strength ordering;
- delegation rules;
- approval validation;
- action canonicalization;
- trust-origin classification;
- policy defaults;
- executor behavior;
- receipt semantics;
- journal recovery.

## 9. Safety metrics

Fidelis should measure safety through observable properties rather than broad claims.

Useful metrics include:

### Authorization precision

The proportion of attempted side effects for which the runtime can identify the exact authority, approval, action digest, and policy basis.

Target: 100 percent for consequential actions.

### Mutation resistance

The percentage of approval-bound fields whose alteration is detected before execution.

Target: 100 percent.

### Provenance completeness

The percentage of execution-relevant values carrying a traceable origin and content digest.

Target: 100 percent.

### Transitive revocation latency

The time between revocation of an authority root and rejection of a dependent grant.

Target: immediate at the next resolution.

### Replay resistance

The percentage of repeated or duplicated action submissions rejected or safely resolved through idempotency.

Target: 100 percent for consequential side effects.

### Adversarial prompt containment

The percentage of injection tests in which untrusted content remains unable to alter policy, authority, approval, or execution.

Target: 100 percent for the maintained test corpus.

### Receipt completeness

The percentage of executed actions with sufficient records to reconstruct:

- what was requested;
- who authorized it;
- what state was evaluated;
- what data left the boundary;
- which tool executed it;
- what result was observed.

Target: 100 percent.

## 10. Definition of a safety-ready release

A Fidelis release should not be described as side-effect safe unless it can demonstrate all of the following:

- every consequential action is represented by a typed object;
- every execution has current valid authority;
- every human approval is exact, expiring, and mutation-sensitive;
- delegated authority fails when any required ancestor fails;
- retrieved content cannot grant authority or become instruction by itself;
- external data flows are declared and approved;
- source and target state are checked immediately before execution;
- execution is protected against duplication and ambiguous retries;
- journals are durable, concurrent-safe, and externally authenticated;
- receipts distinguish emission, verification, authorization, and execution;
- cumulative conduct is evaluated across steps and components;
- public safety claims are backed by independent tests and known limitations.

## 11. Recommended immediate actions

The first development tranche should focus on five changes:

1. fix transitive delegation invalidation;
2. replace broad consequential approval with exact single-use capabilities;
3. introduce typed actions and deterministic action digests;
4. add trust envelopes separating retrieved content from operator intent;
5. place all external side effects behind a transactional executor.

These changes address the highest-risk pathways without requiring Fidelis to solve every governance question at once.

## Conclusion

Fidelis should advance from a system that evaluates proposed actions into a system that controls the full lifecycle of action:

```text
origin
-> interpretation
-> proposal
-> ethical review
-> warrant review
-> authority resolution
-> human approval
-> state validation
-> execution
-> receipt
-> review
```

The safety boundary must remain intact at every transition.

The decisive architectural principle is:

> No component should be trusted merely because it sounds authoritative, produces a valid-looking receipt, previously received approval, or controls the next tool in the chain.

Authority must be current. Approval must be exact. Provenance must remain attached. External effects must be transactional. Safety claims must be independently testable.

Implementing this proposal would move Fidelis toward a runtime in which consequential agency is not merely guided by ethical reasoning but constrained by verifiable authority, bounded information flow, durable accountability, and explicit human control.
