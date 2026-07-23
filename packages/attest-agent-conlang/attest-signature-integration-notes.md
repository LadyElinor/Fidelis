# Attest Signature Integration Notes (Draft)

## Immediate recommendation

For Attest reference implementations, use:
- **Ed25519** for current message signing

Rationale:
- deterministic
- compact
- fast
- well-supported
- matches the protocol's current examples

## Reference implementation guidance

### Canonical signing rule

The verifier and signer must operate over the exact same canonical byte sequence.

Signing target:
- canonicalized envelope fields
- including ordering anchor
- including warrant and lineage content
- excluding only fields explicitly defined as non-identity-bearing by the protocol

### Suggested envelope fields

Future-friendly shape:
- `sig_alg`: e.g. `ed25519`
- `key_id`: stable reference to signer public key
- `sig`: raw signature material or encoded form

## Migration path

### Phase 1
- Ed25519 only

### Phase 2
- hybrid signatures, e.g.:
  - `ed25519`
  - `ml-dsa-44`

### Phase 3
- policy-selectable signature suites for different deployment tiers

## Verification classes

Signature verification belongs to the protocol's hard-guarantee layer.

It can verify:
- origin binding to key material
- message integrity
- canonicalization agreement

It cannot verify:
- truth of warrant claims
- independence of grounds
- semantic validity of opaque payloads

## Later design option

If Attest grows toward committee or quorum attestations, consider a separate extension for:
- threshold or aggregated signatures
- multi-signer endorsement objects
- BLS-style or Schnorr-style aggregation where appropriate

That should remain an extension, not a v0.1/v0.2 requirement.
