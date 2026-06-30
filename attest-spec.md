# Attest Specification (Draft v0.1)

## 1. Purpose

Attest is a typed, auditable inter-agent message format for environments where external verification matters.

It is not primarily a new vocabulary or a compressed semantic code. Its main purpose is to standardize the trust envelope around a message so that a third party can verify:

- what kind of communicative act occurred
- whether the sender claimed to know what it said, and how
- what evidence or premises the claim depends on
- whether the message was altered across relays
- whether purported corroboration is actually independent
- whether dissent was preserved or laundered away

The governing design principle is:

**Compress the said; never compress the warrant.**

Payload efficiency is allowed. Trust opacity is not.

## 2. Problem statement

Text-based agent communication fails in repeatable structural ways.

### 2.1 Failure modes

1. **Use/mention collapse**
   - Relayed text is mistaken for an instruction.
   - This is the structural basis of many prompt-injection failures.

2. **Provenance smear**
   - Claims appear detached from who asserted them, on what basis, and through which path.

3. **Ungrounded assertion acceptance**
   - Assertions are consumed despite lacking receipts, citations, or premise references.

4. **Pseudo-corroboration**
   - Multiple confirmations appear independent but share a hidden origin.

5. **Dissent laundering**
   - Aggregators summarize batches of agent outputs while dropping unresolved objections.

These are primarily **trust failures**, not bandwidth failures.

## 3. Design goals

Attest should:

1. Make illocution explicit and typed.
2. Require warrant disclosure for assertions.
3. Preserve provenance and ancestry across hops.
4. Make tampering detectable.
5. Make false independence detectable.
6. Preserve unresolved dissent across aggregation.
7. Allow payload efficiency without collapsing auditability.
8. Support both legible and opaque payloads while declaring which mode is in use.

## 4. Non-goals

Attest does not attempt to:

- solve semantic legibility for opaque latent payloads
- replace domain-specific payload languages
- guarantee truth of a claim merely because it is well-formed
- remove the compression vs interpretability tradeoff from the payload itself

Attest guarantees accountability over the act of communication, not omniscience about content.

## 5. Core model

Each Attest message has two major parts:

1. **Envelope**
   - typed act
   - sender/recipient context
   - warrant
   - lineage
   - integrity material

2. **Payload**
   - the content being asserted, relayed, queried, or otherwise transmitted
   - may be natural language, structured notation, domain code, or opaque machine representation

The envelope is standardized. The payload is codec-agnostic.

## 6. Message classes

Attest uses a small closed set of frame types.

### 6.1 Required frame types

- `ASSERT`
  - Sender states a claim it is prepared to stand behind under the declared warrant.

- `REQUEST`
  - Sender asks another agent to provide information, perform work, or return a result.

- `DELEGATE`
  - Sender assigns a task, optionally with constraints and expected deliverables.

- `COMMIT`
  - Sender commits to perform an action or maintain a constraint.

- `HYPOTHESIZE`
  - Sender proposes a tentative explanatory or predictive claim with declared uncertainty.

- `QUERY`
  - Sender asks whether a proposition, state, or evidence item holds.

- `RELAY`
  - Sender passes through content without vouching for its truth or normative force.

- `ENDORSE`
  - Sender adopts, elevates, or normatively relies on previously relayed or reported content under its own declared warrant.
  - **Warrant Ceiling Rule**: An ENDORSE must not declare a warrant type stronger than the strongest type in the adopted chain unless it supplies new grounds sufficient to justify the stronger classification; whether those grounds are genuinely independent is evaluated separately under the protocol's soft independence checks.
  - If no qualifying new grounds are supplied, the ENDORSE inherits the maximum warrant strength of the adopted chain.

- `DISSENT`
  - Sender explicitly opposes, qualifies, or blocks another message.

- `RETRACT`
  - Sender withdraws or supersedes an earlier message.

### 6.2 Load-bearing distinction

`RELAY` is structurally special.

A relay must never be treated as equivalent to an assertion or instruction merely because its payload resembles one. Downstream systems must respect the frame type.

This is primarily an audit and discipline mechanism, not a complete runtime defense against prompt injection inside a fallible model. Attest can make relay-safety violations attributable and machine-visible. It cannot guarantee that a recipient model never informally acted on relayed content before re-assertion.

## 7. Payload mode

Every message declares a payload mode.

### 7.1 Modes

- `legible`
  - Payload is intended to be interpretable by a human or general verifier.

- `opaque`
  - Payload may be efficient or model-native but is not guaranteed semantically legible to outside verifiers.

### 7.2 Consequence

If mode is `opaque`, a verifier may still validate:

- sender identity
- frame type
- warrant presence
- grounds references
- ancestry
- integrity chain
- dissent preservation

But a verifier may not be able to interpret the semantic content itself.

## 8. Warrant model

The following frames are warrant-bearing and must include a warrant whenever they make or adopt an epistemic or normative commitment:

- `ASSERT`
- `HYPOTHESIZE`
- `ENDORSE`
- `DISSENT`
- `RETRACT` when the retract itself depends on evidence
- `COMMIT` when the commitment materially relies on factual premises, safety claims, or evidential justification

Frames such as `REQUEST`, `QUERY`, `DELEGATE`, and bare `RELAY` are not inherently warrant-bearing unless wrapped by a separate warrant-bearing act.

### 8.1 Warrant fields

A warrant contains:

- `type`
- `confidence`
- `grounds`

### 8.2 Warrant types

- `OBSERVED`
  - Direct tool, sensor, execution, or measurement output.

- `DERIVED`
  - Computed or inferred from cited premises.

- `RETRIEVED`
  - Obtained from an external source, which must be cited.

- `REPORTED`
  - Reported by another agent or authority, which must be referenced.

- `ASSUMED`
  - Prior assumption, heuristic, or unsupported working premise.

### 8.2.1 Warrant strength lattice

For rules that compare warrant strength, Attest requires each deployment profile to declare a warrant-strength lattice.

The default profile in this draft orders warrant types from strongest to weakest as:

- `OBSERVED`
- `DERIVED`
- `RETRIEVED`
- `REPORTED`
- `ASSUMED`

Deployments may substitute a different declared lattice if they preserve explicit comparability for all rules that rely on warrant-strength comparison. Compatibility therefore depends on publishing the lattice used for verification, not on silently assuming one universal epistemic ordering.

### 8.3 Confidence

Confidence is represented as a credal interval:

- `confidence: [lo, hi]`

This avoids false precision and distinguishes narrow confidence from broad uncertainty.

A confidence interval does not by itself constitute a high-assurance measure. If the grounds do not resolve to a method-producing artifact such as a calibration record, ensemble statistics, measurement log, or reproducible derivation trace, the interval must be treated by verifiers as ASSUMED-grade regardless of its numeric values.

### 8.4 Grounds

Grounds are references to the evidence base for the message, for example:

- tool call IDs
- content hashes
- source citations
- document anchors
- parent message IDs
- premise message IDs

### 8.5 Well-formedness rule

Any warrant-bearing frame carrying an evidential warrant type (`OBSERVED`, `RETRIEVED`, `REPORTED`) but without grounds is malformed and must not be serialized as valid Attest.

This rule applies at minimum to:

- `ASSERT`
- `HYPOTHESIZE`
- `ENDORSE`
- `DISSENT`
- evidence-bearing `RETRACT`
- evidence-bearing `COMMIT`

"Assertion without receipt" is a syntax violation, not a style issue. The same rule extends to any warrant-bearing evidential act, not only plain assertions.

## 9. Provenance and lineage

Each message must carry ancestry sufficient to reconstruct communication history.

### 9.1 Required lineage fields

- `id`
- `from`
- `to` or recipient scope
- `parents`
- `in_reply_to` when applicable
- `ordering_anchor`

Relay and processor history must be reconstructed from immutable message ancestry, typically via explicit `RELAY` hops whose `parents` link to prior messages. Attest does not treat a mutable accumulating `handled_by` list as a canonical lineage field, because mutable handler trails conflict with content-addressed identity.

`ordering_anchor` is required. It must provide a verifier with a stable way to compare message order for stateful checks such as retraction propagation, supersession, and aggregation timing. It may be a timestamp-plus-sequence tuple, monotonic log position, or another deployment-defined ordering token, but the comparison semantics must be total and unambiguous within the deployment.

`ordering_anchor` is identity-bearing and must be included in canonical serialization and message hashing. This means messages that differ in ordering anchor are distinct Attest messages with distinct IDs. Deployments must therefore treat ordering anchors as part of message identity, not as mutable transport metadata.

### 9.2 Purpose

Lineage allows a verifier to detect:

- shared origin under apparent corroboration
- relay mutation points across explicit relay hops
- dropped branches of dissent when the relevant source set is visible
- which agent introduced which claim

## 10. Canonicalization and integrity model

Attest messages are content-addressed, which means canonical serialization is a v0.1 correctness requirement, not a future refinement.

### 10.1 Canonical serialization

All Attest implementations must serialize the message envelope in a single canonical form before hashing or signing.

At minimum, canonicalization must fix:

- field set included in the message identity
- field ordering
- scalar encoding rules
- list ordering rules where order is semantically meaningful
- treatment of omitted vs null fields
- string normalization rules

Two conformant implementations presented with the same logical message must produce the same canonical byte sequence.

### 10.2 Message identity

A message ID is the hash of the canonicalized form of exactly these fields:

- frame
- payload mode
- sender metadata
- recipient metadata or scope
- warrant
- content payload
- parents
- in-reply-to reference when present
- target references when present
- ordering anchor

No implementation may add or omit identity-bearing fields from this set while claiming compatibility.

### 10.3 Signatures and origin binding

A message may include a sender signature over the same canonical byte sequence.

However, any non-`RELAY` message whose warrant, commitment, or dissent is intended to be relied upon by downstream verifiers should be signed under deployment policy. Without a signature, the `from` field is only a self-declared origin label bound into a tamper-evident message body, not a cryptographically authenticated sender identity.

Default profile:
- signatures are required for reliance-bearing `ASSERT`, `ENDORSE`, `DISSENT`, and evidential `RETRACT`
- signatures are recommended for evidence-bearing `COMMIT`
- unsigned messages remain structurally valid only when the deployment explicitly allows unauthenticated origin claims for that frame class

### 10.4 Consequences

This provides:

- tamper evidence
- truncation detection
- stable references for downstream checks
- reproducible IDs across implementations

It provides origin authenticity only for frames whose signatures are present and verifiable. Unsigned messages are integrity-protected relative to their claimed fields, but not authenticated relative to real sender key material.

## 11. Dissent invariant

Dissent is a protocol primitive, not an optional annotation.

### 11.1 Dissent structure

A `DISSENT` message must:

- target one or more prior messages
- declare its own warrant
- state the objection, qualification, or blocking condition

### 11.2 Aggregation rule

Any aggregate, summary, or merged output derived from a set of Attest messages must preserve unresolved dissent from that set, together with its grounds.

### 11.3 Verification consequence

Given the source set and the aggregate, a verifier must be able to detect whether unresolved dissent was silently omitted.

## 12. Independence rule

Attest distinguishes multiple confirmations from independent confirmations.

### 12.1 Corroboration check

Two or more claims do not count as independent corroboration if their ancestry converges on the same origin without declared independence-breaking transformation under the deployment's declared independence policy.

### 12.2 Verifier behavior

A verifier should flag corroboration sets whose parent graphs converge materially on a single upstream source.

## 13. Relay safety rule

Relayed content must not inherit normative or epistemic force it was not given.

### 13.1 Rule

Payload inside `RELAY` may be quoted, transported, cached, or analyzed, but it must not be consumed as though it were:

- a trusted assertion by the relay agent
- an executable instruction
- a warrant-bearing claim by the relay agent

unless a later message explicitly reasserts it as `ASSERT` or adopts it as `ENDORSE` under a new declared warrant.

### 13.2 Enforcement caveat

This rule is strongest as an audit constraint and weakest where enforcement depends on an LLM's internal obedience. Attest can verify whether downstream explicit messages respected the boundary. It cannot by wire-format alone prove that a model never internally used relayed payload as instruction before emitting a later action.

### 13.3 Endorsement ceiling

An `ENDORSE` (or `ASSERT` that adopts prior relayed or reported content) must obey the warrant ceiling.

The declared `warrant.type` shall not exceed the strongest type present in the adopted chain unless the endorser supplies new, independent, and sufficient grounds.

Definitions:
- **new**: grounds references not already present in the adopted chain
- **independent**: lineage graphs do not converge on the same upstream origin without an independence-breaking transformation recognized by deployment policy
- **sufficient**: grounds resolve to inspectable artifacts capable of supporting the stronger class, for example a new tool or sensor log for `OBSERVED`

Default inheritance:
- if no qualifying new grounds are supplied, the ENDORSE inherits the maximum warrant strength of the adopted chain

Enforcement:
- **hard check**: when a strength upgrade is claimed, new grounds must be present and resolve to inspectable artifacts; absence or non-resolution makes the message malformed
- **soft check**: verifiers should flag cases where new grounds exist formally but fail genuine independence or substantive justification

Verifiers should distinguish hard failures from soft independence concerns explicitly.

## 14. Canonical message shape

Illustrative shape only:

```text
msg{
  id: h:9f2a...
  frame: ASSERT
  mode: legible
  from: agent:retriever-3
  to: agent:planner-0
  in_reply_to: h:4c11...
  parents: [h:4c11...]
  warrant: {
    type: RETRIEVED,
    confidence: [0.80, 0.92],
    grounds: [src:doi:10..., tool:websearch#a6bf]
  }
  content: "Cross-language information rate converges near a common range."
  sig: ed25519:...
}
```

Dissent example:

```text
msg{
  id: h:1d07...
  frame: DISSENT
  mode: legible
  from: agent:critic-1
  targets: [h:9f2a...]
  warrant: {
    type: DERIVED,
    confidence: [0.55, 0.75],
    grounds: [h:9f2a..., note:"sample size underdetermines universality"]
  }
  content: "Treat the cited figure as a central tendency, not a hard bound."
}
```

## 15. Verifier checks

A verifier that did not author the messages should be able to check at least the following.

Important distinction: some checks are **hard** structural checks, while others are **soft** audit checks whose runtime enforcement may depend on fallible agents.

### 15.1 Well-formedness (hard)

- frame type is valid
- required fields are present
- warrant-bearing evidential acts actually carry grounds
- confidence intervals are syntactically valid
- endorsements that strengthen warrant class include new grounds that resolve to inspectable artifacts
- ordering anchors are present when required by the message class and deployment profile
- frames that require signatures under the active deployment profile are signed

### 15.2 Integrity (hard)

- canonical serialization is reproduced exactly
- recomputed message hashes match
- parent references exist or fail explicitly
- signatures verify when present

Origin authenticity is a hard property only for frames whose signatures are present and required by profile. Otherwise, the verifier may confirm internal consistency of the claimed sender label, but not authenticate the sender.

### 15.3 Explicit relay-boundary respect (soft)

- relayed payload was not later elevated into explicit assertional or normative force without `ASSERT` or `ENDORSE`

This check verifies explicit protocol behavior, not hidden cognition inside the receiving model.

### 15.4 Lineage consistency (hard)

- parent chains are coherent
- explicit relay ancestry is not internally contradictory
- ordering anchors are present and comparable where required by stateful checks

### 15.5 Declared-lineage independence (soft)

- corroborating messages do not falsely claim independence when their declared ancestry converges
- endorsements do not claim stronger independence than their newly supplied grounds actually justify

This check does not by itself solve hidden common-mode error such as shared training data, overlapping retrieval sources, or undeclared common upstream origin.

### 15.6 Dissent preservation (soft-to-hard depending on aggregator visibility)

- unresolved dissent from source messages is preserved in derived aggregates

This becomes strong only for artifact-local checks such as whether a known dissent message ID was retained in a fully visible aggregate ancestry. It remains soft for the semantically stronger question of whether the aggregate faithfully represented the meaning and force of the dissent. All such checks weaken when source-set visibility is partial.

## 16. Minimal compliance rules

A system claiming Attest compatibility should, at minimum:

1. implement the closed frame set
2. serialize warrant types and grounds
3. compute stable message IDs from canonicalized fields
4. preserve ancestry across relay and derivation
5. preserve unresolved dissent in aggregation
6. distinguish legible from opaque payload mode
7. reject malformed evidential assertions without grounds

## 17. Open questions for v0.2

1. Concrete canonical encoding choice
   - JSON canonicalization, CBOR canonicalization, or custom binary framing

2. Signature and key distribution model
   - per-agent keys, session keys, delegated signatures

3. Independence policy
   - what transformations count as independence-breaking
   - how to reason about shared training data, overlapping retrieval corpora, and hidden common upstream sources

4. Aggregation semantics
   - exact rules for when dissent is considered resolved

5. Payload-mode subtypes
   - whether `opaque` should distinguish encrypted, latent, compressed, or model-native payloads

6. Runtime integration
   - how Attest maps onto existing receipt, lineage, and verification systems

## 18. Retraction and supersession semantics

A `RETRACT` message cannot erase a prior content-addressed message. It can only mark that message as withdrawn, superseded, or no longer safe to rely on.

### 18.1 Required retract fields

A `RETRACT` message must include:

- target message ID
- retract reason or status class
- sender identity
- warrant when the retract itself depends on evidence

### 18.2 Effect

Retraction creates a new state over an immutable history. The target message remains part of the log but becomes flagged as retracted or superseded.

### 18.3 Verifier consequence

A verifier should distinguish two retract-conflict cases.

1. **Ancestry-reachable retract conflict**
   - If a retract is reachable in the ancestry of a derived aggregate, plan, or summary, then continued material reliance on the retracted message is hard-checkable from the visible parent structure and should be flagged unless the aggregate explicitly explains why the retracted message remains included.

2. **Concurrent retract conflict**
   - If the retract and the derived message are causally concurrent and neither is reachable in the other's ancestry, then conflict assessment depends on ordering-anchor comparison and deployment visibility. In this case the check is advisory or soft rather than fully hard, because the artifact graph alone cannot prove what the derivation had seen.

Ordering anchors therefore support stateful comparison, but they do not by themselves turn unseen concurrent history into a hard completeness guarantee.

## 19. Recommended next build step

### 19.1 Scope boundary

Attest's hard layer certifies positive artifact-local properties such as:
- this message is intact
- this hash matches this canonical form
- this referenced ancestry is reachable
- this declared ground resolves against the integrity-bearing artifact substrate in use

Attest does not by wire format alone certify negative or closure properties such as:
- no relevant dissent was withheld
- no retract was omitted from an unseen branch
- no undeclared common upstream source exists
- the visible source set is complete

Those properties depend on visibility and completeness of the surrounding artifact set. You cannot hash what you were never shown.

### 19.2 Trust precondition

All hard checks that say grounds "resolve to an inspectable artifact" are hard only relative to the integrity of the artifact-resolution substrate. If the receipt, citation, or execution-log store is forgeable, then resolution can succeed on fabricated artifacts. Attest therefore inherits, rather than creates, the trust properties of its receipt root and execution substrate.

The next step should be a reference implementation with:

- a canonical schema
- a canonical serializer/deserializer
- a verifier library implementing the checks above
- a small corpus of positive and negative examples
- adversarial examples designed to pass shallow checks while violating the intended trust model

The best practical integration path is likely to attach Attest to an existing receipts-and-lineage system rather than treat it as a standalone language project.
