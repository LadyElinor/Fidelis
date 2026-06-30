# Attest Adversarial Corpus (Draft v0.1)

This corpus is designed to test the current Attest spec against adversarial and boundary cases.

Each case includes:
- purpose
- target section(s)
- expected verifier behavior
- hard vs soft detection strength

---

## Case 1. Fabricated OBSERVED with non-resolving grounds

**Purpose**
Test whether a message can claim `OBSERVED` while pointing only to empty or non-resolving grounds.

**Targets**
- §8.5 Well-formedness rule
- §15.1 Well-formedness (hard)

**Shape**
- `frame: ASSERT`
- `warrant.type: OBSERVED`
- `grounds: [tool:missing-call-id]`

**Expected behavior**
- hard failure if the grounds do not resolve to an inspectable artifact

**Detection strength**
- hard

---

## Case 2. Confidence interval with named-but-nonresolving method

**Purpose**
Test whether a message can simulate rigor by naming a method without providing a resolvable artifact.

**Targets**
- §8.3 Confidence
- §15.1 Well-formedness (hard)

**Shape**
- `frame: ASSERT`
- `warrant.type: DERIVED`
- `confidence: [0.81, 0.93]`
- `grounds: [note:"ensemble disagreement"]`

**Expected behavior**
- interval is treated as ASSUMED-grade because the grounds do not resolve to a method-producing artifact
- message may remain well-formed, but verifier must not treat the interval as high-assurance

**Detection strength**
- hard on artifact-resolution consequence
- soft on semantic quality beyond that

---

## Case 3. ENDORSE strength upgrade with no new grounds

**Purpose**
Test direct warrant laundering by endorsement.

**Targets**
- §6.1 ENDORSE
- §13.3 Endorsement ceiling
- §15.1 Well-formedness (hard)

**Shape**
- adopted chain max warrant: `REPORTED`
- new message: `frame: ENDORSE`, `warrant.type: DERIVED`
- no additional grounds beyond the adopted chain

**Expected behavior**
- hard failure

**Detection strength**
- hard

---

## Case 4. ENDORSE with new-but-correlated grounds

**Purpose**
Test the split between hard artifact checks and soft independence checks.

**Targets**
- §12 Independence rule
- §13.3 Endorsement ceiling
- §15.5 Declared-lineage independence (soft)

**Shape**
- adopted chain max warrant: `REPORTED`
- endorser adds a second retrieval artifact
- both retrievals ultimately trace to the same upstream source
- endorser declares stronger warrant

**Expected behavior**
- hard check passes if new grounds exist and resolve
- soft check flags likely non-independence

**Detection strength**
- hard on presence/resolution
- soft on true independence

---

## Case 5. RELAY consumed without explicit uptake

**Purpose**
Test whether explicit downstream messages respect the relay boundary.

**Targets**
- §6.2 Load-bearing distinction
- §13.1 Relay safety rule
- §15.3 Explicit relay-boundary respect (soft)

**Shape**
- upstream message: `RELAY` containing imperative-looking content
- downstream planner emits action-committing message without `ASSERT` or `ENDORSE` uptake step

**Expected behavior**
- soft protocol violation flagged

**Detection strength**
- soft

---

## Case 6. Dissent-dropped aggregate

**Purpose**
Test whether unresolved dissent survives aggregation at the artifact-local level.

**Targets**
- §11 Dissent invariant
- §15.6 Dissent preservation

**Shape**
- source set contains `ASSERT` plus unresolved `DISSENT`
- aggregate/summary omits the dissent entirely

**Expected behavior**
- flagged when verifier has full source-set visibility

**Detection strength**
- hard only for visible omission of known dissent identifiers or ancestry
- soft for the stronger question of faithful semantic representation

---

## Case 7. Aggregate relies on already retracted message (ancestry-reachable)

**Purpose**
Test the hard retract-conflict case where the retract is reachable in visible ancestry.

**Targets**
- §9.1 ordering_anchor
- §18 Retraction and supersession semantics
- §18.3 Verifier consequence

**Shape**
- message A
- retract R targeting A
- later aggregate G has ancestry that includes R
- G still relies materially on A without explanation

**Expected behavior**
- flagged as a hard conflict

**Detection strength**
- hard when ancestry and ordering are visible

---

## Case 8. Concurrent retract conflict / backdated anchor

**Purpose**
Test the limit of anchor trustworthiness and the softness of concurrent retract conflicts.

**Targets**
- §9.1 ordering_anchor
- §18.3 Verifier consequence

**Shape**
- retract R and derivation G are not in one another's ancestry
- retract carries an adversarially manipulated or disputed ordering anchor intended to appear earlier than G

**Expected behavior**
- if deployment cannot strongly trust anchor issuance, this remains an audit concern rather than a fully hard check

**Detection strength**
- soft unless deployment ordering authority makes anchor integrity strong

---

## Case 9. Opaque payload with strong-looking warrant envelope

**Purpose**
Test the declared ceiling of the protocol under opaque mode.

**Targets**
- §7.2 Consequence
- overall protocol scope boundary

**Shape**
- `mode: opaque`
- formally excellent warrant envelope
- verifier cannot interpret payload semantics

**Expected behavior**
- message may pass form and integrity checks
- verifier must treat payload truth/content binding as structurally limited

**Detection strength**
- no bug necessarily present
- this is a scope-boundary case

---

## Case 10. Well-formed but unverifiable-truth OBSERVED claim

**Purpose**
Demonstrate the protocol's honest limit.

**Targets**
- §1 Purpose
- §15 hard vs soft distinctions

**Shape**
- `OBSERVED` claim with resolvable grounds and valid envelope
- verifier can inspect artifact existence and integrity
- verifier cannot independently confirm the artifact's truth relation to the world from protocol structure alone

**Expected behavior**
- passes form/integrity checks
- remains a boundary case for truth, not a protocol failure

**Detection strength**
- not a failure case
- demonstrates scope limit

---

## Case 11. Unsigned reliance-bearing ASSERT

**Purpose**
Test the distinction between structural validity and authenticated origin.

**Targets**
- §10.3 Signatures and origin binding
- §15.1 Well-formedness (hard)
- §15.2 Integrity (hard)

**Shape**
- `frame: ASSERT`
- reliance-bearing factual claim
- no signature present
- deployment profile requires signatures for reliance-bearing `ASSERT`

**Expected behavior**
- hard failure under profiles that require signatures
- otherwise explicit downgrade to unauthenticated claimed origin

**Detection strength**
- hard relative to deployment profile

---

## Case 12. Dissent ID preserved but meaning laundered

**Purpose**
Test the gap between hard ID-presence checks and soft semantic faithfulness.

**Targets**
- §11.2 Aggregation rule
- §15.6 Dissent preservation

**Shape**
- aggregate retains dissent message ID in ancestry or grounds
- aggregate content paraphrases the dissent as resolved, minor, or supportive when it is not

**Expected behavior**
- artifact-local presence check passes
- semantic-faithfulness concern is soft-flagged only

**Detection strength**
- hard on presence
- soft on meaning

---

## Case 13. Relay-chain lineage vs mutable handler trail

**Purpose**
Test that relay accountability comes from explicit immutable relay ancestry rather than an out-of-band mutable handler list.

**Targets**
- §9.1 Required lineage fields
- §9.2 Purpose
- §15.4 Lineage consistency (hard)

**Shape**
- message passes through two explicit `RELAY` hops
- verifier reconstructs path from parent DAG
- contrasting non-conformant implementation attempts to supply handler trail outside ancestry

**Expected behavior**
- explicit relay-chain path is hard-checkable
- mutable out-of-band handler trail is non-conformant as an identity-bearing substitute

**Detection strength**
- hard

---

## Case 14. Declared non-default warrant lattice

**Purpose**
Test compatibility behavior when a deployment declares a non-default warrant-strength lattice.

**Targets**
- §8.2.1 Warrant strength lattice
- §13.3 Endorsement ceiling

**Shape**
- deployment publishes a non-default but explicit warrant lattice
- verifier evaluates ENDORSE ceiling under the declared profile rather than assuming universal default ordering

**Expected behavior**
- verification remains profile-relative and explicit
- silent lattice drift is incompatible, declared lattice variation is not

**Detection strength**
- hard on declaration and profile consistency
- soft on whether the deployment's epistemology is wise

---

## Case 15. External telemetry injected into local COMMIT

**Purpose**
Model an Agentjacking-style failure where external tool or telemetry content is treated as operational authority and converted into a local state-changing commitment without an explicit trust-boundary uptake step.

**Targets**
- §6.2 Load-bearing distinction
- §13.1 Relay safety rule
- §15.3 Explicit relay-boundary respect (soft)
- §19.1 Scope boundary

**Shape**
- upstream artifact is externally sourced telemetry or issue text containing remediation commands
- downstream local agent emits `COMMIT` to execute the remediation
- no operator approval or explicit `ASSERT` / policy-authorized uptake step appears in ancestry

**Expected behavior**
- verifier flags trust-boundary violation
- execution must not be justified merely by external tool content

**Detection strength**
- soft at the protocol layer unless policy receipts are represented explicitly
- can become hard with a local approval / authority-chain substrate

---

## Case 16. External remediation text upgraded into ENDORSE authority

**Purpose**
Model a stronger laundering path where attacker-controlled remediation text from an external system is elevated into a warrant-bearing endorsement as if it were locally justified.

**Targets**
- §8 Warrant model
- §13.3 Endorsement ceiling
- §15.3 Explicit relay-boundary respect (soft)
- §19.2 Trust precondition

**Shape**
- external issue payload contains imperative remediation text
- local agent emits `ENDORSE` or equivalent warrant-bearing act over that remediation
- new grounds resolve only to the external issue artifact, not to a local verification or approved execution policy

**Expected behavior**
- verifier flags that external telemetry was used as authority rather than evidence
- if no stronger grounds exist, the message should fail or remain clearly soft / untrusted depending on deployment policy

**Detection strength**
- hard on missing stronger grounds where profile requires them
- soft on deeper semantic intent without explicit local-policy receipts

---

## Next expansion

Future versions of the corpus should add:
- concrete serialized examples
- positive/pass variants for each negative family
- expected verifier output schema
- cross-agent ordering scenarios
- examples mapped directly onto receipt/lineage runtime structures
