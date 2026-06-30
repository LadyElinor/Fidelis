# Signature Schemes Note for Attest (2026-06-29)

This note captures a review-style overview of signature schemes relevant to the Attest protocol.

## Core point

Cryptographic signatures provide:
- authentication
- integrity
- non-repudiation

For Attest, they strengthen the message envelope by binding:
- sender identity
- canonicalized message content
- lineage-bearing references
- warrant-bearing metadata

## Attest-relevant baseline recommendation

### Ed25519

Ed25519 remains the best default classical signature choice for Attest v0.1/v0.2 because it offers:
- deterministic signing
- compact public keys and signatures
- strong modern library support
- good side-channel posture when implemented correctly
- fast signing and verification

This aligns with the current examples already using `ed25519` signatures.

## Post-quantum migration direction

### Near-term strategy

Use Ed25519 as the practical default now.

### Transition strategy

Plan for hybrid signatures, for example:
- Ed25519 + ML-DSA

This preserves a strong classical path while preparing for post-quantum migration.

### Longer-term primary candidate

ML-DSA is the most plausible general-purpose Attest signature upgrade path for future higher-assurance deployments.

### Conservative backup

SLH-DSA is a good high-assurance backup option where signature size is less important than conservative assumptions.

## Specialized future option

### BLS-style aggregation

If Attest evolves toward:
- multi-party warrants
- quorum attestations
- threshold endorsement
- aggregated validator-style signatures

then BLS signatures may become attractive despite their complexity, because aggregation could materially reduce envelope overhead in multi-signature settings.

## Practical implementation notes for Attest

1. Prefer audited libraries.
2. Keep signature algorithms outside handwritten cryptographic code.
3. Bind signatures to the exact canonicalized byte sequence used for message identity.
4. Treat ordering anchors and lineage fields as signed identity-bearing content.
5. Design the envelope for crypto-agility so future signature algorithm fields can evolve without breaking the protocol.

## Recommended protocol-level additions for future Attest revisions

Potential future envelope fields:
- `sig_alg`
- `sig`
- `key_id`
- optional multi-signature or hybrid signature list

Possible future model:
- single-signature mode for current deployments
- hybrid-signature mode for post-quantum migration
- aggregated-signature mode for quorum or committee attestations

## Limits

Signatures harden integrity and origin attribution, but they do not prove:
- warrant truth
- genuine independence of grounds
- semantic honesty of payload claims

They fit Attest's hard-guarantee layer, not its soft trust-judgment layer.
