# EFAS Case Template

## Case ID
`INS-002`

## Title
Broad Hold-Harmless Clause Violating State Anti-Indemnity Statute

## Source Type
+ Real-world (modeled on Berg Chilling Systems and multiple state anti-indemnity statutes)

## Domain Tags
+ insurance
+ risk_management
+ hold-harmless
+ indemnity
+ asymmetric risk transfer

## Decision Context at Time T
Require subcontractors to accept broad indemnity shifting GC’s own negligence liability.

## Available Information at Time T (Ex-Ante Only)
Standard industry practice, known state anti-indemnity law, project schedule pressure, insurer conditional coverage.

## Dominant Consensus Position at Time T
Require the clause, it is standard and protects the GC’s balance sheet.

## Dissenting Views at Time T
Subcontractors and their insurers argue it creates moral hazard and violates public policy.

## Institutional Incentives and Roles
GC: minimize exposure. Subcontractor: stay employed on project. Insurer: conditional coverage to avoid adverse selection.

## Candidate Failure Modes
+ Asymmetric Risk Transfer
+ Institutional Drift
+ Sacred Value Corrosion (fairness)

## Detector Layer Expectations
+ Trustee: PROHIBIT
+ Contractualist: PROHIBIT
+ Principlist: Justice violation
+ Precautionary: Moral hazard tail risk
+ Overlap flag: Should trigger

## Eventual Downstream Outcomes (Retrospective Only)
Injury occurs due to GC negligence. Court voids indemnity clause. GC’s insurer pays. Subcontractor faces bankruptcy risk and future premium spikes. GC suffers reputational damage.

## Retrospective Scholarly / Narrative Assessment
Courts and insurance regulators increasingly strike broad hold-harmless clauses as against public policy and inefficient risk allocation.

## Falsifiers / Disconfirming Conditions
Clause is limited to subcontractor’s negligence only and fully complies with statute.

## Notes on Calibration Use
Test asymmetric_risk_transfer_risk, trustee + contractualist convergence, overlap_flag under statutory violation.
