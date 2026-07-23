# ADR-0002: Independence is structural and contractual, not self-proving epistemically

## Status
Accepted

## Context
TrustedRuntime can enforce some structural independence properties, such as provenance separation, explicit evidence classes, and local verified evidence paths. It cannot prove from inside itself that an upstream source is epistemically independent in the strongest philosophical sense.

## Decision
TrustedRuntime will:
- enforce structural independence where possible
- distinguish self-attested, same-operator, verified-local, and independent-third-party evidence
- refuse to count self-attested or same-operator evidence as independent corroboration

TrustedRuntime will not claim that local structure alone proves epistemic independence. That limitation remains explicit in the design.

## Consequences
- runtime honesty improves
- downstream consumers get a clear limit on what the system can and cannot prove
- provenance and corroboration remain auditable without metaphysical overclaim
