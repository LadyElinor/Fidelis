# Attest Spec Review Notes (2026-06-29)

This note captures the strongest critique received against `attest-spec.md` draft v0.1.

## Meta constraint

The critique correctly notes a structural limitation: a design cannot validate its own independence from within the same ancestry chain. Any feedback from the original authoring line is self-review, not independent validation.

## Most important substantive critique

### 1. Audit vs enforcement strength is blurred

The spec currently treats some guarantees as if they are verified at the same strength level.

In reality:
- integrity and well-formedness are strong verifier-checkable properties
- relay safety, type safety, and independence are only partially machine-checkable and may collapse to audit-only if enforcement lives inside a fallible model

The spec should explicitly distinguish:
- **hard guarantees**: cryptographic or structural checks
- **soft guarantees**: auditable protocol violations, but not necessarily preventable at runtime

### 2. RELAY typing is not a full prompt-injection defense

Typing RELAY creates a valuable boundary and audit hook, but it does not prevent a model from reading relayed text and informally acting on it inside the forward pass.

So Attest can:
- make relay misuse attributable
- require explicit re-assertion for normative uptake

But Attest cannot, by wire format alone, guarantee that the recipient model did not internally treat relayed content as instruction.

### 3. Independence detection is underspecified

The current lineage-based check only catches declared shared-origin cases.

It does not solve correlated error from:
- shared training data
- overlapping retrieval corpora
- multiple citations with one hidden upstream source
- common-mode reasoning failures

This is not a minor refinement. It is where most of the substantive content of the independence claim lives.

### 4. Warrant labels and confidence intervals can simulate rigor without instrumenting it

Self-declared warrant types are weak unless their grounds resolve to inspectable artifacts.

Confidence intervals especially should not be treated as meaningful unless grounded in a declared method such as:
- calibrated model output
- ensemble disagreement
- measurement statistics
- reproducible computation

Otherwise they should default to low-assurance interpretation.

### 5. The spec gives strongest guarantees to the easiest problems

Content-addressing and signatures are strong but may not target the highest-value failure modes.

The parts that map most directly to the motivating trust failures remain softer and more audit-oriented.

This inversion should be acknowledged explicitly.

## Foundational blockers identified

### A. Canonicalization cannot remain deferred

A content-addressed protocol cannot leave canonical serialization unspecified.

Without fixed canonicalization:
- IDs are not reproducible across implementations
- cross-implementation references break
- signatures become ambiguous

### B. Endorsement semantics are underspecified

The spec relies on explicit reassertion or endorsement of relayed content, but the frame system did not previously define endorsement behavior clearly enough.

Needed:
- either a dedicated `ENDORSE` frame
- or a precise rule that `ASSERT` referencing a relayed payload and adding warrant counts as endorsement

### C. RETRACT propagation is underspecified

In an append-only content-addressed system, a retract cannot erase prior messages.

Needed:
- supersession/tombstone semantics
- verifier behavior for aggregates that still depend on retracted messages
- explicit status resolution rules

## Strong parts worth preserving

- use/mention distinction as first-class type
- "Compress the said; never compress the warrant"
- declared `legible` vs `opaque` mode
- dissent as a protocol invariant
- refusal to overclaim semantic legibility for opaque payloads

## Recommended next steps

1. Fix correctness blockers first:
   - canonicalization
   - endorsement semantics
   - retract propagation

2. Then write an adversarial corpus designed to defeat the verifier, including:
   - fabricated OBSERVED warrants
   - lineage laundering
   - dissent-dropping aggregates
   - retracted-message reuse
   - opaque payload with misleading grounds

3. Then distinguish hard vs soft guarantees throughout the verifier section.
