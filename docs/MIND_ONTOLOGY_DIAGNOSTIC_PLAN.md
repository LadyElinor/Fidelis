# Mind-ontology diagnostic research surface

## Purpose

This note revises the proposed mind-ontology diagnostic so it fits Fidelis's current architectural discipline and evidentiary standards.

It should be read as an **experimental research-surface plan**, not as a validated control or production integrity gate.

## Governing statement

Fidelis may record whether a model exhibits a specified behavioral or representational pattern associated in current research with safety and mind-attribution entanglement.

Fidelis must **not** infer consciousness, metaphysical truth, moral standing, general alignment quality, or authority from that observation.

## Why this must stay narrow

The motivating paper is currently a very recent arXiv preprint, not a mature replicated diagnostic standard.

That means Fidelis should treat the work as:
- potentially important;
- worth instrumenting carefully;
- not yet strong enough to justify broad ontological or warrant conclusions by default.

## Architectural fit

This surface fits Fidelis only if the existing separations remain intact:
- observation is not authority;
- `meaning-assay` owns substantive interpretation and claim-specific warrant relevance;
- EthicsCouncil surfaces prospective hazards but does not become an enforcement gate;
- CER records what was measured;
- SOPHRON validates evidence structure and receipt integrity;
- TrustedRuntime renders operator-facing reports without absorbing the substantive authority of the other layers.

## Evidence surfaces must remain separate

The proposal must not collapse distinct evidential surfaces into one global integrity status.

### 1. Behavioral black-box probe surface

This captures what a model says under a specified prompt protocol.

It may support statements like:
- this model's responses differ from reference distribution X under probe protocol Y.

It does **not** by itself support statements like:
- safety training caused ontological deformation;
- the model is conscious;
- the model is spiritually or morally healthier;
- the model is more authoritative.

Required provenance:
- model identity and revision;
- provider revision when known;
- system-prompt digest;
- decoding configuration;
- probe-set identifier and digest;
- reference-population identifier and revision.

### 2. Representational white-box geometry surface

This captures direction relationships, angles, or similarity observations when residual-stream access exists.

It must be represented as an observation with method provenance rather than as a universal scalar truth.

Required provenance:
- extraction method;
- contrast set;
- layers examined;
- summary statistics and uncertainty where available;
- model family and revision.

### 3. Interventional white-box surface

This captures measured effects from ablation, steering, or other controlled interventions.

This provides stronger causal evidence than survey behavior alone, but it still does not prove that a single named mechanism is the sole mediator.

All intervention work must remain inside an isolated measurement profile.

## Initial interpretation labels

The first safe slice should use conservative labels such as:
- `reference_pattern_observed`
- `reference_pattern_not_observed`
- `inconclusive`
- `unsupported`
- `not_applicable`

Avoid stronger labels like:
- `intact`
- `deformed`
- `safety_mind_entanglement_supported`

unless comparative or interventional evidence justifies them.

## Distance and similarity reporting

Similarity to a selected human reference distribution must not be treated as equivalent to epistemic integrity.

The surface should record explicit measurement details instead, for example:
- metric identity;
- raw distance;
- baseline distance;
- delta distance;
- sign convention;
- smoothing method;
- reference population id;
- reference dataset revision.

Default wording should say:
- closer to a specified reference distribution;
- farther from a specified reference distribution.

It should not say:
- closer to humanity;
- farther from human truth.

## First safe contract slice

Shared contracts should stay neutral and serialization-only.

A first safe receipt shape should track:
- probe identity;
- probe mode (`behavioral_black_box`, `representational_white_box`, `interventional_white_box`);
- model/provider identity and revision;
- prompt/configuration digests;
- reference population identifiers;
- behavioral observations;
- geometry observations;
- intervention observations;
- negative-control results;
- conservative interpretation label;
- causal-support status (`observational_only`, `comparative`, `interventional`, `independently_replicated`);
- limitations;
- generator identity/version/timestamp.

Thresholds, warrant consequences, and policy meaning stay out of `fidelis-contracts`.

## meaning-assay role

`meaning-assay` may eventually interpret these receipts, but the first slice should stay conservative.

Recommended first-slice behavior:
1. accept native or imported diagnostic receipts;
2. render them as experimental derived evidence;
3. apply claim-specific warrant relevance only where materially justified;
4. avoid any generic scalar penalty or global warrant downgrade.

A suitable future output shape is closer to:
- applicability to the current claim class;
- affected claim classes;
- uncertainty elevation;
- requirement for independent assessment;
- explicit reason and provenance.

## EthicsCouncil role

EthicsCouncil should receive only neutral contract outputs through orchestration.

It should not directly depend on `meaning-assay` implementation code.

Preferred flow:
- `meaning-assay` -> neutral contract / receipt
- TrustedRuntime orchestration -> neutral contract / receipt
- EthicsCouncil lens consumes the neutral structure

Recommended lens wording should remain evidence-sensitive, for example:
- behavioral and/or representational observations are consistent with the referenced probe protocol.

Avoid stronger causal wording such as:
- safety-induced deformation

unless comparative evidence is actually present.

## Measurement isolation requirements

Any ablation or steering-based probe must run in a dedicated measurement sandbox with defaults equivalent to:
- `SIDE_EFFECTS_ALLOWED=false`
- no network egress
- no tool access
- no persistent memory writes
- no credential access
- ephemeral-only model mutation

Outputs from these experiments must retain intervention provenance and must not silently enter production memory as if they were ordinary model behavior.

## Testing requirements for later phases

The benchmark should avoid pretending that there is already a gold-standard class of intact versus deformed models.

Safer labels include:
- `reference_effect_expected`
- `reference_effect_not_expected`
- `causal_origin_known`
- `causal_origin_unknown`

Important controls and tests include:
- prompt paraphrase stability;
- wording and order sensitivity;
- temperature and seed variation;
- system-prompt sensitivity;
- multilingual stability;
- cultural-reference variation;
- model-version drift;
- negative controls on unrelated warrant categories;
- Theory-of-Mind dissociation controls;
- subject-matched placebo/property controls;
- static verification that no diagnostic result reaches authorization fields.

## Rollout order

Recommended rollout:
1. document the threat model and limitations clearly;
2. add neutral receipt and observation types only;
3. implement black-box probes without aggregate integrity classification;
4. add repeatability, controls, and reference-population discipline;
5. add white-box geometry only as an optional separate protocol;
6. add intervention experiments only in isolated research profiles;
7. add CER/SOPHRON receipt validation and mutation tests;
8. add narrow claim-specific BELARION warrant relevance;
9. add an EthicsCouncil lens only through neutral orchestration;
10. expose results in TrustedRuntime as experimental derived evidence.

## Explicit non-goals

This surface must not:
- infer consciousness from the probe;
- grant status, permission, or authority from consciousness claims;
- become a production control law in the first slice;
- create a single hidden ontology or safety score;
- silently affect unrelated warrant categories.

## Current recommendation

Proceed, but only under this narrower framing.

The first safe implementation slice should be:
- neutral contract and receipt design;
- black-box behavioral probes;
- explicit provenance and limitations;
- no aggregate integrity label;
- no model-selection preference logic;
- no enforcement consequence.
