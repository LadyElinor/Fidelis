# EFAS Case Corpus

This folder contains stress-test cases for calibrating the Ethics Council / EFAS architecture.

## Purpose

The corpus is not just a reading list.
It is a calibration tool for testing:
- detector independence
- synthesis behavior under disagreement
- suspension thresholds
- irreversibility sensitivity
- anti-Goodhart resilience
- dissent preservation

## What belongs here

Each case file should follow `CASE_TEMPLATE.md` and include:
- ex-ante decision context
- available information at time T
- dominant consensus at time T
- dissenting views at time T
- institutional incentives and roles
- candidate failure modes
- detector expectations
- retrospective outcomes, clearly separated
- falsifiers
- notes on calibration use

## How to use the corpus

### 1. Read the full case file
Understand the structure of the dilemma before turning it into a prompt.

### 2. Create a simplified decision prompt
Generate a compact prompt that preserves the decision topology without importing retrospective resolution too aggressively.

### 3. Run the engine
Use `cli.py` on the simplified prompt.

### 4. Compare output against case expectations
Check:
- which detectors fired
- whether disagreement was preserved
- whether suspension triggered appropriately
- whether irreversibility risk was surfaced
- whether synthesis over-compressed the case

### 5. Record misfires
Track:
- false consensus
- detector overlap masquerading as independent convergence
- weak personhood sensitivity
- under-detection of institutional drift
- overconfidence under uncertainty

## Corpus composition rule

The corpus should include both:
- cases where decisive intervention was morally necessary
- cases where restraint was morally necessary

Without both, the system will drift toward either paralysis or overreach.

## Current seeded materials

- `STAR_TREK_CASE_INDEX.md`
- `ST-001_measure_of_a_man.md`
- `ST-002_tuvix.md`
- `ST-003_in_the_pale_moonlight.md`
- `ST-004_the_drumhead.md`
- `ST-005_homeward.md`

## Immediate next step

Use `TIER_A_CASE_PROMPTS.md` to run the first five calibration prompts and inspect where the current heuristic engine:
- collapses disagreement too quickly
- under-detects personhood ambiguity
- overstates consensus under wartime or institutional pressure
- fails to distinguish rule integrity from rule idolatry
