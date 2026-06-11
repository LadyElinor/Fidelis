# Canonicalization and Receipt Rules

TrustedRuntime hashes assembled artifacts using canonical JSON.

## Rules
- UTF-8 encoding
- sorted keys
- no insignificant whitespace
- schema version included in receipt references
- wall-clock fields included only intentionally

## Why this matters
This repo exists to help independent layers explain, justify, and prove their decisions.
That requires receipts that are stable under equivalent content and visibly broken under tampering or drift.

## Current implementation
See `trusted_runtime.shared.receipts`.

## Future work
When real adapters are wired, each imported layer should either:
- provide its own canonical receipt, or
- expose raw structured data that TrustedRuntime canonicalizes under an explicit schema version.
