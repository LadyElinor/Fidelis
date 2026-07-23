# Attest v0.1 Review Summary (2026-06-29)

## Overall verdict

Attest v0.1 is a strong foundation with a clear ceiling and an actionable hardening path.

The central design principle remains the correct one:

**Compress the said; never compress the warrant.**

The review judges that the protocol meaningfully improves auditability and trust-claim traceability for multi-agent systems without pretending that a wire format can directly prove truth.

## Preserved strengths

- first-class use/mention via `RELAY`
- mandatory warrant + grounds
- lineage + content-addressing
- dissent preservation invariant
- declared `legible` vs `opaque` mode
- closed illocution set
- clear non-goals

## Key remaining themes

### 1. ENDORSE ceiling is useful, but narrower than early summaries implied

The review affirms that warrant laundering through `ENDORSE` is the right hardening surface, but the hard gain is limited to cases where:

- no genuinely new grounds are supplied, or
- the supplied grounds fail artifact resolution

The remaining questions of genuine independence and substantive sufficiency stay soft or policy-dependent.

### 2. Ordering anchor must be identity-bearing, but does not solve concurrency by itself

The review correctly treats retract and supersession ordering as dependent on a required and hashed ordering anchor, while also recognizing that concurrent retract conflicts remain visibility-dependent rather than fully hard-checkable from the wire format alone.

### 3. Confidence intervals require artifact-backed grounding

A confidence interval should be treated as ASSUMED-grade unless its grounds resolve to a method-producing artifact.

### 4. Hard vs soft guarantees are a design ceiling, not just a polish issue

The review emphasizes an important general limit:

- Attest can make trust claims well-formed, attributable, tamper-evident, and auditable
- Attest cannot itself make those trust claims true
- Attest hard-checks positive artifact-local properties, not closure or completeness of unseen history

That boundary should remain explicit in future revisions.

### 5. Origin authenticity is conditional on signatures

Attest binds claimed sender fields into integrity-protected messages, but cryptographic origin authenticity only holds when the relevant frame is signed under the deployment profile.

## Recommended next artifacts

1. adversarial corpus
2. reference implementation
3. direct receipt/lineage integration sketch

## Suggested next spec-level tightening

The strongest spec-level tightenings from this pass were:

- replace mutable handler trails with relay ancestry reconstructed from explicit `RELAY` hops
- enumerate all warrant-bearing frames, not only `ASSERT` / `HYPOTHESIZE`
- require signatures for reliance-bearing frames under the default profile
- split ancestry-reachable retract conflicts from concurrent retract conflicts
- treat the warrant ordering as a declared deployment lattice rather than one fixed universal total order
