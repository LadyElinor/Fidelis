# Bayesian Weight Tuning Appendix

EFAS v0.1 Extension

## Purpose

This appendix defines the intended logic for calibrating detector-layer weights over time.

The central rule is:
**weights should track independent diagnostic contribution, not agreement with prevailing consensus.**

This is a specification artifact, not yet a live engine feature.

---

## Core Bayesian Framing

Each detector layer has a provisional weight representing its expected diagnostic usefulness in synthesis.

The update target is not:
- agreement with historical human judgment
- agreement with current majority output
- rhetorical plausibility

The update target is:
- independent hazard detection
- early warning utility
- robustness under adversarial pressure
- cross-case reliability

In formal terms, each layer should be treated as having a probability distribution over reliability rather than a fixed moral authority score.

---

## Evidence Types That Should Update Weights

Ranked roughly by strength:

### 1. Independent Hazard Detection
A layer correctly flags a material hazard that other layers systematically missed.

### 2. Early Warning Utility
A layer surfaces a risk before the consequences become obvious or irreversible.

### 3. False Positive / False Negative Trade-off
A layer is especially valuable when it avoids false negatives in high-stakes cases, even if that comes with some low-stakes noise.

### 4. Adversarial Robustness
A layer continues to detect real problems even when the surrounding system launders, obscures, or proceduralizes the hazard.

### 5. Cross-Regime / Cross-Cultural Consistency
A layer performs usefully across multiple institutional settings rather than only within one moral style or one era's consensus assumptions.

---

## Negative Evidence That Should Down-Weight a Layer

- repeated mimicry of prevailing consensus without independent signal
- failure to detect hazards that other layers consistently catch
- excessive false positives that drown meaningful warnings
- post-hoc rationalization masquerading as ex-ante detection

---

## Operational Mechanics (Deferred Specification)

When live calibration becomes justified, the system should support:

- equal or weakly informed priors at initialization
- case-by-case evidence scoring
- damped updates rather than rapid swings
- normalization after updates
- rolling or decayed influence of older evidence
- transparent logging of all update rationales

Suggested evidence dimensions per case:
- independent signal score
- lead-time score
- false-positive / false-negative assessment
- adversarial robustness score
- cross-context transfer confidence

---

## Explicit Falsifier for the Tuning System

If a layer that repeatedly detects real hazards missed by consensus is down-weighted *because* it diverges from consensus, then the tuning mechanism has failed its purpose.

This is the most important self-audit rule in the weighting system.

---

## Implementation Constraint

Dynamic weighting should **not** be implemented as a serious live feature until the project has:

- a sufficiently diverse stress-test corpus
- structured case evaluations
- logged calibration outcomes
- reviewable evidence for updates

Before those exist, live reweighting would be pseudo-Bayesian theater.

---

## Near-Term Use

For now, this appendix should guide:
- corpus design
- calibration logging
- future auditability requirements
- review of whether the synthesis engine is rewarding conformity instead of useful dissent
