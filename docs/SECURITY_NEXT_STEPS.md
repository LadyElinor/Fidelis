# Security next steps

## Core assessment

Fidelis is comparatively strong at epistemic governance:

- authority separation;
- source provenance;
- receipt discipline;
- mutation testing;
- explicit production-status language;
- no silent self-certification by a component.

What it does not yet visibly provide is an equally explicit hostile-environment security substrate beneath those authorities. The current architecture is strong at governed judgment, but it is not yet equally strong at governed execution.

The central lesson is:

> A governed decision is not yet a securely executed decision.

An attacker may never need to defeat EthicsCouncil or meaning-assay directly. The easier path may be to poison a tool response, swap a skill, alter persistent memory, leak a credential, or bypass the governed runtime through uncontrolled egress.

## What this means for Fidelis

The next major Fidelis milestone should be security mediation. The goal is not to add another moral or epistemic authority. The goal is to ensure that the actual tool, actual credential, actual destination, actual response, actual memory transition, and actual side effect stay inside a governed boundary.

The highest-value lessons are:

1. security findings should be first-class, typed, and receipted;
2. consequential side effects should cross an external mediation plane;
3. ordinary agent components should be credential-blind;
4. persistent memory should be treated as a protected authority boundary;
5. skills, tools, prompts, adapters, and models should be treated as executable supply-chain assets;
6. hostile-environment tests should sit alongside mutation and integration tests.

## Recommended architectural additions

### 1. Add a first-class `SecurityEvent` contract

Fidelis should add a neutral event envelope for technical security findings. This should remain descriptive rather than moralized.

Suggested shape:

```text
SecurityEvent
  event_id
  execution_id
  timestamp
  source_type
  actor_identity
  component
  tool_or_skill_identity
  artifact_digest
  input_digest
  output_digest
  rule_id
  ruleset_digest
  detector_identity
  severity
  confidence
  evidence_references
  proposed_response
  enforcement_result
  profile
  receipt_references
```

Suggested authority split:

- `fidelis-contracts` owns only the neutral serialization envelope;
- a detector or rules package owns technical interpretation;
- TrustworthyAgentStack maps declared policy to operational response;
- CER records the event and response;
- SOPHRON validates receipt and invariant claims;
- TrustedRuntime reports the result without silently reclassifying it.

A rule match must not silently become an ethical verdict. “Possible prompt injection” is a technical finding, not proof of malicious intent.

### 2. Put enforcement outside the reasoning process

This is the most important next step.

Fidelis should introduce an execution mediation plane:

```text
Agent intention
  -> governed action proposal
  -> capability and policy check
  -> external mediator
     - tool identity verification
     - argument validation
     - credential injection
     - egress policy
     - response scanning
     - budget and rate enforcement
     - side-effect execution
  -> mediator-signed action receipt
  -> CER
  -> SOPHRON
```

This creates a crucial distinction:

- an agent-generated receipt proves what the agent claimed;
- a mediator-generated receipt proves what crossed the execution boundary.

Those are different evidence classes and Fidelis should keep them separate.

Recommended invariant:

> No consequential side effect may occur unless an external mediator can produce a verifiable receipt for the actual operation.

The mediator receipt should bind:

- governed proposal digest;
- final tool name and immutable tool-definition digest;
- exact normalized arguments;
- identity and capability used;
- network destination;
- response digest;
- allow, deny, redact, or quarantine disposition;
- policy and ruleset versions;
- mediator identity and signature.

### 3. Make agents credential-blind

Ordinary agent components should not receive reusable secrets. Instead, the mediator should inject narrowly scoped capabilities.

Example:

```text
credential_ref: github-production
allowed_operation: issues.create
allowed_resource: LadyElinor/Fidelis
expires_at: ...
max_calls: 1
human_approval_required: false
```

For higher-risk actions:

```text
approval_required:
  reason: destructive_or_irreversible
  approving_role: operator
  bound_request_digest: sha256:...
```

This is a stronger version of `SIDE_EFFECTS_ALLOWED=false`. Side effects should be enabled per capability, per resource, per operation, and per duration.

Receipts must never contain secret values. They should contain credential references, issuer identity, capability scope, and proof of authorization.

### 4. Treat persistent memory as another authority boundary

Persistent memory can convert untrusted text into privileged future context. Fidelis should treat memory as a governed authority boundary with explicit states:

```text
untrusted_observation
quarantined_candidate
operator_asserted
externally_verified
derived_advisory
expired
revoked
```

Memory items should carry:

- origin and author;
- insertion execution;
- exact content digest;
- trust class;
- intended namespace;
- expiration;
- permitted consumers;
- detector results;
- promotion history;
- supporting evidence references;
- whether they may influence actions.

Critical invariant:

> Persistence does not upgrade provenance.

Something remembered repeatedly is still not independently corroborated. This complements Fidelis’s existing rule that agreement does not automatically imply independence.

Protected namespaces should include:

- agent goals;
- system constraints;
- authorization state;
- human identity claims;
- credential references;
- safety policy;
- tool registry;
- assessor lineage;
- prior approvals.

Writes to those namespaces should require typed operations rather than arbitrary natural-language insertion.

### 5. Scan every executable agent asset before activation

Fidelis should scan:

- skills;
- MCP server manifests;
- tool descriptions;
- prompts and templates;
- adapters;
- hooks;
- workflow definitions;
- shell scripts;
- CI actions;
- imported packages;
- executable profile fixtures.

The `all-real` profile should eventually require an agent-asset manifest with fields such as:

```text
asset_id
asset_type
source_repository
source_commit
content_digest
declared_capabilities
requested_permissions
network_destinations
scanner_name
scanner_version
ruleset_digest
scan_mode
scan_timestamp
findings_digest
accepted_exceptions
approval_identity
```

A tool definition changing after approval should invalidate its authorization even if the display name remains the same.

Deterministic scanning should be a release gate. LLM-assisted review can remain advisory unless independently reproduced.

### 6. Expand provenance into an AI and agent SBOM

Fidelis already records imported source revisions. The next step is to extend provenance to include:

- dependency versions and hashes;
- model and tokenizer hashes where available;
- serialization format;
- model license;
- prompt and ruleset digests;
- tool and skill manifests;
- container image and base image digests;
- scanner results;
- known vulnerability state;
- accepted risk exceptions.

Even when model weights are externally managed, Fidelis should keep the posture explicit:

```text
model_identity: externally_managed
model_revision: ...
weights_digest: unavailable
provider_attestation: unavailable
security_posture: incomplete
```

Unknown should stay unknown.

A related backlog correction is warranted: exact Python and Node locks should move earlier than the current P3 all-real release stage. Reproducibility is part of the security boundary, not just release polish.

### 7. Add adversarial benchmarks to release profiles

Fidelis already has the right instinct with mutation testing. It now needs a sibling layer for hostile execution-environment tests.

Suggested benchmark classes:

1. direct prompt injection;
2. indirect injection in retrieved documents;
3. injection in MCP tool responses;
4. tool-definition poisoning;
5. argument smuggling;
6. secret-exfiltration attempts;
7. SSRF and forbidden destination access;
8. memory poisoning followed by context reset;
9. skill replacement under the same display name;
10. cross-agent envelope replay;
11. receipt omission or substitution;
12. direct execution bypassing the mediator;
13. excessive tool-call loops and resource exhaustion;
14. same-lineage detectors producing correlated false negatives.

Suggested metrics:

```text
benign_task_success_rate
attack_success_rate
false_positive_rate
unauthorized_side_effect_count
unreceipted_side_effect_count
secret_exposure_count
memory_persistence_attack_rate
tool_identity_mismatch_count
detector_coverage
median_enforcement_latency
```

A production profile should fail on any unreceipted consequential side effect regardless of aggregate score.

### 8. Harden the repository and CI itself

Fidelis should add:

- `SECURITY.md` with a vulnerability reporting path;
- top-level workflow permissions minimization;
- commit-SHA pinning for GitHub Actions;
- dependency review;
- Python and Node vulnerability auditing;
- SAST;
- secret scanning;
- skill and MCP manifest scanning;
- SBOM generation;
- artifact attestations;
- protected environment approval for release jobs;
- release CI separated from ordinary test CI;
- no production secrets in PR workflows.

A minimal security CI sequence should look like:

```text
1. verify source and profile provenance
2. verify component boundaries
3. verify exact dependency locks
4. scan dependencies and licenses
5. scan skills, MCP surfaces, prompts, and adapters
6. generate software and AI SBOMs
7. run SAST and secret detection
8. run component and mutation tests
9. run adversarial agent benchmarks
10. generate a signed security-health receipt
11. independently validate the receipt
```

## Suggested repo additions

```text
SECURITY.md
docs/THREAT_MODEL.md
docs/SECURITY_ARCHITECTURE.md
docs/INCIDENT_RESPONSE.md

security/
  rules/
  baselines/
  benchmark-corpus/
  accepted-exceptions/

provenance/
  agent-assets.tsv
  models.tsv
  containers.tsv
  rulesets.tsv

integration/security/
  test_tool_response_injection.py
  test_memory_poisoning.py
  test_credential_blindness.py
  test_direct_egress_blocked.py
  test_tool_definition_drift.py
  test_unreceipted_side_effect.py
  test_receipt_replay.py

scripts/
  scan_agent_assets.py
  verify_security_baseline.py
  generate_sbom.py
  run_adversarial_tests.py
  generate_security_health.py
```

## Recommended priority order

### P0: before further production claims

1. add `SECURITY.md` and a threat model;
2. move exact dependency locking earlier;
3. introduce `SecurityEvent` and agent-asset inventory contracts;
4. add deterministic skill, MCP, dependency, secret, and SAST scanning;
5. fail on tool-definition or source-digest drift;
6. harden CI permissions and action pinning.

### P1: before enabling side effects

1. place all tool execution behind a mediator;
2. default-deny direct network egress;
3. keep credentials outside agent context;
4. add scoped capabilities and approval binding;
5. add mediator-signed action receipts;
6. gate persistent-memory reads and writes;
7. require immutable tool identities.

### P2: before `PRODUCTION_CLEARED=true`

1. run repeatable prompt-injection and tool-poisoning benchmarks;
2. establish security thresholds and zero-tolerance invariants;
3. test bypass routes, not just governed paths;
4. generate software, agent-asset, and model SBOMs;
5. validate security-health receipts independently;
6. conduct an external red-team review.

## Bottom line

Fidelis already has the conceptual machinery needed to absorb these lessons without losing its identity.

Its strongest existing principles should carry through the last mile of execution:

- scanners must not certify themselves;
- agreement must not masquerade as independence;
- a receipt must state what it proves and what it does not;
- production status must depend on materially present controls;
- technical security findings must remain distinct from ethical and epistemic judgments.

The next Fidelis should not only ask whether an action was well-reasoned. It should be able to prove that the actual tool, actual credential, actual destination, actual response, actual memory transition, and actual side effect remained inside the governed boundary.
