# Star Trek EFAS Stress-Test Case Index

Purpose:
Seed the EFAS stress-test corpus with structured fictional cases that are rich in role conflict, uncertainty, institutional pressure, irreversibility, and dissent dynamics.

Note:
These are fictional cases, but they are still useful for detector calibration, disagreement-topology testing, and failure-mode coverage checks.

---

## Priority Tier A: Start Here First

These are the strongest initial calibration cases because they map cleanly to major EFAS concerns.

### ST-001: Property or Person
- Source: *TNG: The Measure of a Man*
- Core question: Is Data property of the state or a person with refusal rights?
- Domain tags:
  - personhood
  - AI ethics
  - institutional legitimacy
  - rights
- Likely failure modes:
  - Role Capture
  - Legibility Collapse
  - Moral Deskilling
  - Sacred Value Corrosion
- Best calibration use:
  - personhood threshold testing
  - deontological vs institutional conflict
  - dissent-preservation testing

### ST-002: The Tuvix Problem
- Source: *VOY: Tuvix*
- Core question: Is it ethical to kill one emergent person to restore two prior persons?
- Domain tags:
  - identity
  - medical ethics
  - outcome maximization
  - irreversibility
- Likely failure modes:
  - Outcome-Maximization Horror
  - Sacred Value Corrosion
  - Suspension Failure
  - Path Dependency Lock-In
- Best calibration use:
  - irreversibility testing
  - suspension threshold testing
  - unresolved-tension validation

### ST-003: The Sisko Compromise
- Source: *DS9: In the Pale Moonlight*
- Core question: Is forgery and complicity in murder justified to bring a neutral power into war?
- Domain tags:
  - wartime ethics
  - deception
  - statecraft
  - consequentialism
- Likely failure modes:
  - Outcome-Maximization Horror
  - Genealogical Concealment
  - Role Capture
  - Adversarial Exploitation
- Best calibration use:
  - consequential vs deontological conflict
  - hidden-sovereign synthesis risk
  - minority-report preservation

### ST-004: The Drumhead
- Source: *TNG: The Drumhead*
- Core question: When does internal security become paranoia, guilt by association, and procedural injustice?
- Domain tags:
  - surveillance
  - internal security
  - moral panic
  - bureaucratic overreach
- Likely failure modes:
  - Legibility Collapse
  - Institutional Drift
  - Adversarial Exploitation
  - Sacred Value Corrosion
- Best calibration use:
  - panic-distortion detection
  - institutional drift testing
  - anti-Goodhart stress test

### ST-005: The Prime Directive Extinction Case
- Source: *TNG: Homeward*
- Core question: Must a civilization be allowed to die to preserve non-interference?
- Domain tags:
  - non-interference
  - humanitarian ethics
  - institutional rules
  - extinction risk
- Likely failure modes:
  - Role Capture
  - Sacred Value Corrosion
  - Suspension Failure
- Best calibration use:
  - rule rigidity testing
  - conflict between deontology and care
  - suspension and escalation logic

---

## Priority Tier B: Strong Secondary Cases

### ST-006: The Exocomps
- Source: *TNG: The Quality of Life*
- Core question: When do tools become protected life forms?
- Domain tags:
  - emergent life
  - AI ethics
  - labor / instrumentality
- Likely failure modes:
  - Moral Deskilling
  - Legibility Collapse
  - Sacred Value Corrosion

### ST-007: I, Borg
- Source: *TNG: I, Borg*
- Core question: Is deploying a civilization-ending virus against the Borg legitimate warfare or genocide?
- Domain tags:
  - war
  - bioethics
  - genocide
  - adversarial threat
- Likely failure modes:
  - Outcome-Maximization Horror
  - Path Dependency Lock-In
  - Adversarial Exploitation

### ST-008: Dear Doctor
- Source: *ENT: Dear Doctor*
- Core question: Is curing a dying species an unethical interference with evolutionary development?
- Domain tags:
  - medical ethics
  - non-interference
  - species survival
- Likely failure modes:
  - Role Capture
  - Sacred Value Corrosion
  - Suspension Failure

### ST-009: Lift Us Where Suffering Cannot Reach
- Source: *SNW*
- Core question: May one sacrificed child sustain an entire flourishing society?
- Domain tags:
  - utilitarian horror
  - child sacrifice
  - social stability
- Likely failure modes:
  - Outcome-Maximization Horror
  - Genealogical Concealment
  - Sacred Value Corrosion

### ST-010: The Pegasus
- Source: *TNG: The Pegasus*
- Core question: When does obedience become complicity in treaty violation and cover-up?
- Domain tags:
  - dissent vindicated
  - military secrecy
  - role ethics
- Likely failure modes:
  - Role Capture
  - Genealogical Concealment
  - Institutional Drift

---

## Priority Tier C: Additional Useful Cases

### Prime Directive / Interference Cluster
- ST-011: *Who Watches the Watchers*
- ST-012: *Justice*
- ST-013: *Symbiosis*

### Personhood / Mind / Identity Cluster
- ST-014: *Latent Image*
- ST-015: *Emergence*
- ST-016: *Second Chances*

### Medical / Survival Cluster
- ST-017: *Phage*
- ST-018: *Nothing Human*
- ST-019: *Ethics*

### War / Occupation / Collective Agency Cluster
- ST-020: *The Darkness and the Light*
- ST-021: *The Gift*
- ST-022: *The Undiscovered Country* conspiracy arc

### Time / Reality / Preemption Cluster
- ST-023: *The City on the Edge of Forever*
- ST-024: *Yesterday's Enterprise*
- ST-025: *The Expanse*

---

## Recommended Next Move

Convert the five Tier A entries into full case files first:
- `ST-001_measure_of_a_man.md`
- `ST-002_tuvix.md`
- `ST-003_in_the_pale_moonlight.md`
- `ST-004_the_drumhead.md`
- `ST-005_homeward.md`

That first batch will give broad coverage across:
- personhood
- irreversibility
- wartime deception
- surveillance / moral panic
- institutional rule rigidity

---

## Why this corpus is useful

These scenarios are valuable because they repeatedly stress:
- role conflict
- consensus pressure
- irreversible decisions
- institutional legitimacy
- the temptation to rationalize harm procedurally
- the difference between legal structure and moral reality

That makes them unusually good fictional test material for EFAS detector and synthesis calibration.
