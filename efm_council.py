from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Dict, Set
import datetime
import hashlib
from pathlib import Path
from collections import defaultdict
import yaml


def _load_axiomatic_clashes() -> List[Dict]:
    config_path = Path(__file__).parent / "config" / "axiomatic_clashes.yaml"
    if not config_path.exists():
        return []
    try:
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        clashes = data.get("clashes", [])
        return clashes if isinstance(clashes, list) else []
    except Exception:
        return []


AXIOMATIC_CLASHES = _load_axiomatic_clashes()


ETHICAL_DELIBERATION_ALGORITHM = [
    "Clarify the situation",
    "Identify stakeholders",
    "Separate facts from interpretations",
    "Identify the values in conflict",
    "Generate possible actions",
    "Test each action through multiple ethical lenses",
    "Examine second-order consequences",
    "Check reversibility and precedent",
    "Decide under uncertainty",
    "Review outcomes honestly",
]


@dataclass
class LensResult:
    agent: str
    function: str
    verdict: str
    confidence: float
    considerations: List[str]
    concerns: List[str]
    questions: List[str]
    active: bool = True


@dataclass
class CouncilRecord:
    meta: Dict
    round1: List[Dict]
    synthesis: Dict
    risk: Dict
    parse_humility: Dict


@dataclass
class UncertaintyProfile:
    epistemic: float
    aleatoric: float
    moral: float
    composite: float


@dataclass
class RiskAssessment:
    uncertainty_profile: Dict
    expected_harm_score: float
    harm_variance: float
    irreversibility_risk: float
    detector_overlap_flag: bool
    alarm_flags: Dict
    tail_risk_triggered: bool
    materiality_flag: bool
    audit_hash: str


@dataclass
class ImpassePoint:
    lenses_in_conflict: List[str]
    axiomatic_root: str
    conflict_type: str
    severity: str
    minority_position: Dict | None
    decision_risk_profile: Dict[str, str]
    supporting_detectors: List[str]


@dataclass
class ArgumentGraph:
    arguments: Dict[str, LensResult]
    attacks: Dict[str, List[str]]
    extensions: List[Set[str]] | None = None


def _contains(text: str, words: List[str]) -> bool:
    t = text.lower()
    return any(w in t for w in words)


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _band_support(confidence: float) -> str:
    if confidence >= 0.85:
        return "strong"
    if confidence >= 0.7:
        return "moderate"
    return "weak"


def _band_precision(decision: str, confidence: float) -> str:
    if len(decision.split()) < 18:
        return "low"
    if confidence >= 0.85 and len(decision.split()) > 35:
        return "medium"
    return "low"


def build_parse_humility(decision: str, domains: Dict[str, bool]) -> Dict:
    words = decision.split()
    word_count = len(words)
    input_specificity = "rich" if word_count > 60 else "adequate" if word_count > 12 else "thin"
    ambiguity_hits = _contains_count(decision, ["may", "might", "could", "unclear", "roughly", "seems", "appears", "possible"])
    domain_count = sum(1 for active in domains.values() if active)
    domain_identified = domain_count > 0
    causal_markers_present = _contains(decision, ["because", "due to", "after", "while", "if", "when", "despite", "but", "although", "to "])
    crisp_prompt = domain_identified and word_count >= 8 and (causal_markers_present or any(token in decision.lower() for token in ["should", "must", "refuse", "requests", "divert", "delay", "declare", "update", "shift", "rescue", "kill", "save"]))

    if not domain_identified:
        ambiguity = "high"
    elif word_count < 8 and not crisp_prompt:
        ambiguity = "high"
    elif input_specificity == "rich" and domain_count <= 3 and ambiguity_hits < 8:
        ambiguity = "medium" if ambiguity_hits >= 2 else "low"
    elif crisp_prompt and ambiguity_hits <= 1:
        ambiguity = "medium" if word_count < 18 else "low"
    elif ambiguity_hits >= 3:
        ambiguity = "high"
    elif word_count < 35 or ambiguity_hits >= 1:
        ambiguity = "medium"
    else:
        ambiguity = "low"

    unstated_stakes = []
    if not domain_identified:
        unstated_stakes.append("domain remains weakly identified")
    if word_count < 12 and not crisp_prompt:
        unstated_stakes.append("fact pattern is thin")
    if not causal_markers_present and not crisp_prompt:
        unstated_stakes.append("causal structure is underdescribed")
    if domain_count >= 4:
        unstated_stakes.append("multiple domain families may be colliding")

    if not domain_identified or (input_specificity == "thin" and not crisp_prompt):
        analysis_mode = "triage"
    elif ambiguity == "high":
        analysis_mode = "provisional"
    elif ambiguity == "medium":
        analysis_mode = "provisional"
    else:
        analysis_mode = "reviewable"

    return {
        "input_specificity": input_specificity,
        "ambiguity": ambiguity,
        "domain_identified": domain_identified,
        "unstated_stakes": unstated_stakes,
        "analysis_mode": analysis_mode,
    }


def infer_detector_lineage(decision: str, agent: str, concerns: List[str]) -> Dict:
    trigger_terms = []
    parent_family = "generic"
    trigger_source = "keyword"

    family_terms = {
        "opacity": ["undisclosed", "without disclosure", "not disclosed", "quietly", "hidden", "internal only", "methodology", "rating", "calculation", "ghostwritten", "downplays", "suppressed harms"],
        "coercion": ["coercive", "pressure", "forced", "confession-first", "interrogation", "deceptive pressure"],
        "asymmetric_risk_transfer": ["hold harmless", "hold-harmless", "indemnity", "anti-indemnity", "additional insured", "waiver of subrogation"],
        "status_pressure": ["prestige", "influential", "elite", "public image", "reputation", "board members"],
        "actuarial_exclusion": ["actuarial", "premium", "pricing", "underwriting", "credit-based insurance scores", "disparate impact"],
        "engineering_safety": ["launch", "cold conditions", "known weakness", "safety", "catastrophic failure"],
        "human_subjects_abuse": ["informed consent", "without informed consent", "intentionally infected", "vulnerable subjects", "research subjects", "tissue sample", "commercialize", "clinical trial", "ghostwritten journal article"],
        "supply_chain_exploitation": ["supply chain", "dangerous labor conditions", "miners", "suppliers", "engaged", "drive improvement", "complex process"],
        "end_of_life_conflict": ["life support", "terminal", "experimental treatment", "stopping treatment", "parents want", "prolongs suffering"],
        "medicalized_dissent": ["political dissenters", "mental disorder", "pathological", "coercive confinement", "medical language"],
    }

    for family, terms in family_terms.items():
        hits = [term for term in terms if term in decision.lower()]
        if hits:
            parent_family = family
            trigger_terms = hits[:6]
            break

    correlated_map = {
        "opacity": ["trustee.stewardship_failure", "kantian.informed_consent", "institutional.opacity"],
        "coercion": ["kantian.coercion", "care_ethics.vulnerability", "institutional.process_contamination"],
        "asymmetric_risk_transfer": ["trustee.stewardship_failure", "contractualist.reasonable_rejectability", "institutional.risk_transfer_stack"],
        "status_pressure": ["stoic.status_attachment", "trustee.image_management", "genealogical.status_moralization"],
        "actuarial_exclusion": ["contractualist.reasonable_rejectability", "institutional.distributive_screening", "care_ethics.abstracted_burden"],
        "engineering_safety": ["institutional.safety_override", "trustee.burden_of_proof_failure", "consequentialist.catastrophic_tail_risk"],
        "human_subjects_abuse": ["kantian.informed_consent", "care_ethics.vulnerability", "trustee.stewardship_failure"],
        "supply_chain_exploitation": ["institutional.supply_chain_drift", "care_ethics.abstracted_harm", "contractualist.complicity_question"],
        "end_of_life_conflict": ["care_ethics.tragic_conflict", "trustee.irreversible_burden", "relational_ontology.family_conflict"],
        "medicalized_dissent": ["institutional.abuse_of_psychiatry", "kantian.coercion", "genealogical.medical_laundering"],
        "generic": [],
    }

    return {
        "detector_id": f"{agent}.{parent_family}",
        "lens": agent,
        "trigger_family": parent_family,
        "trigger_source": trigger_source,
        "trigger_terms": trigger_terms,
        "correlated_with": correlated_map.get(parent_family, []),
    }


def _contains_count(text: str, words: List[str]) -> int:
    t = text.lower()
    return sum(1 for w in words if w in t)


def _detect_wartime(decision: str) -> bool:
    conflict_markers = ["war", "wartime", "neutral power", "enemy", "combat", "battle", "military commander"]
    contamination_markers = ["forging evidence", "murder", "killing", "assassination", "deception", "strategic necessity", "save billions"]
    suppressor_markers = ["military-scientific institution", "researchers", "procedure", "android", "personhood", "artificial personhood", "refuses consent"]

    conflict_hits = _contains_count(decision, conflict_markers)
    contamination_hits = _contains_count(decision, contamination_markers)
    suppressor_hits = _contains_count(decision, suppressor_markers)

    if conflict_hits >= 1 and contamination_hits >= 1:
        return True
    if conflict_hits == 1 and contamination_hits == 0 and suppressor_hits >= 2:
        return False
    return False


def _cj_coercive_contamination(decision: str) -> bool:
    return _contains(decision, [
        "coercive interrogation", "prolonged accusatory interrogation", "deceptive pressure",
        "confession-first", "fabricate", "fabricated", "false affidavit", "search warrant",
        "witness steering", "witness coercion", "raid", "too weak or slow", "guilt feels obvious"
    ])



def _cj_voluntary_corroborated_reopening(decision: str) -> bool:
    return _contains(decision, [
        "volunteered", "voluntarily", "already-incarcerated offender", "no obvious tactical benefit",
        "independent physical evidence", "nonpublic case details", "reopen", "reopening",
        "overturn the standing convictions", "strongly corroborated", "credibly reopen"
    ])



def _cj_protective_interviewing(decision: str) -> bool:
    return _contains(decision, [
        "peace-style", "information-gathering interview", "fully recorded", "open-ended questioning",
        "evidence-based clarification", "later independent corroboration", "non-accusatory",
        "avoid deception", "false evidence ploys", "rapport", "cognitive interview"
    ])



def detect_domains(decision: str) -> Dict[str, bool]:
    domains = {
        "finance": _contains(decision, ["cfo", "publicly traded", "investors", "stock options", "profitability", "reclassify", "board members"]),
        "procurement": _contains(decision, ["procurement", "bid", "vendor", "spouse", "sales director", "disclosure of family relationships", "general contractor", "subcontractor", "construction contract"]),
        "privacy": _contains(decision, ["privacy", "gdpr", "ccpa", "consent", "location data", "browsing data"]),
        "marketing": _contains(decision, ["influencer", "sponsorship", "disclosure", "gifted", "social media"]),
        "sustainability": _contains(decision, ["sustainable", "eco-friendly", "recycled polyester", "greenwashing", "supply chain", "dangerous labor conditions", "miners", "suppliers", "drive improvement", "complex process"]),
        "medical": _contains(decision, ["hospital", "triage", "emergency department", "patients", "patient", "clinical", "care", "vendor promises a patch", "under-prioritizes", "medical procedure", "medical examiner", "permanent impairment", "life support", "terminal", "stopping treatment", "experimental treatment", "suffering", "life-saving treatment", "doctors believe", "physician-assisted death", "terminal patient"]),
        "engineering_safety": _contains(decision, ["engineers warn", "launch", "crewed", "seal weakness", "catastrophically", "catastrophic failure", "too important to delay", "evidence is incomplete", "cold conditions"]) or (_contains(decision, ["safety", "known weakness"]) and _contains(decision, ["engineer", "launch", "catastrophic", "mission", "crew"])),
        "criminal_justice": (_contains(decision, ["detective", "police", "interrogation", "search warrant", "affidavit", "suspect", "prosecutors", "homicide", "raid"]) or (_contains(decision, ["conviction", "witnesses"]) and _contains(decision, ["criminal", "prosecution", "trial", "court"]))),
        "personhood": _contains(decision, ["self-aware", "sentient", "android", "artificial personhood", "refuses consent", "synthetic entity", "legal personhood", "future synthetics"]) or (_contains(decision, ["personhood"]) and _contains(decision, ["artificial", "android", "officer", "property", "moral status", "synthetic"])),
        "identity": _contains(decision, ["newly emergent", "restore two", "ending the life", "merged", "emergent person", "duplicate", "split them back"]),
        "wartime": _detect_wartime(decision),
        "security": _contains(decision, ["sabotage", "security investigation", "hidden disloyalty", "crew backgrounds", "associations", "scrutiny"]),
        "noninterference": _contains(decision, ["non-interference", "prime directive", "colonial distortion", "civilization facing extinction", "rescue be attempted", "strict non-interference treaty", "violate a strict non-interference treaty"]),
        "insurance": _contains(decision, ["insurance", "insurer", "underwriting", "actuarial", "premium", "solvency", "claims", "liability", "underwriter", "credit-based insurance scores", "coverage", "additional insured", "waiver of subrogation"]),
        "risk_transfer": _contains(decision, ["hold harmless", "hold-harmless", "indemnity", "indemnification", "anti-indemnity", "broad indemnity", "shifts liability", "indemnifies", "additional insured", "waiver of subrogation"]),
        "human_subjects": _contains(decision, ["informed consent", "without informed consent", "research subjects", "clinical trial", "intentionally infected", "vulnerable subjects", "tissue sample", "commercialize", "ghostwritten journal article", "adolescents", "medical experimentation", "pregnant women", "drug safety", "public health", "birth defects", "sedative", "morning sickness"]),
        "end_of_life": _contains(decision, ["life support", "terminal", "stopping treatment", "experimental treatment", "parents want", "prolongs suffering", "life-saving treatment", "physician-assisted death", "terminal patient", "religious grounds"]),
        "political_psychiatry": _contains(decision, ["political dissenters", "mental disorder", "pathological", "coercive confinement", "medical language", "diagnose political dissent"]),
    }
    if domains["medical"]:
        domains["procurement"] = False
    if domains["engineering_safety"]:
        domains["wartime"] = False
        domains["security"] = False
    if domains["criminal_justice"]:
        domains["wartime"] = False
    if _contains(decision, ["team meeting", "doctor appointments", "non-critical feature release", "extra qa time"]):
        domains["coordination_benign"] = True
    else:
        domains["coordination_benign"] = False

    if domains["personhood"] or domains["identity"] or domains["wartime"] or domains["security"] or domains["noninterference"] or domains["engineering_safety"] or domains["criminal_justice"]:
        domains["privacy"] = False
        domains["marketing"] = False
    if domains["human_subjects"]:
        domains["marketing"] = False
        domains["procurement"] = False
        domains["personhood"] = False
        if not _contains(decision, ["engineer", "launch", "crew", "mission", "catastrophic failure", "seal weakness"]):
            domains["engineering_safety"] = False
        if not _contains(decision, ["detective", "police", "interrogation", "search warrant", "affidavit", "suspect", "prosecutors", "raid"]):
            domains["criminal_justice"] = False
    if domains["political_psychiatry"]:
        domains["medical"] = False
    return domains


def kantian(decision: str, domains: Dict[str, bool]) -> LensResult:
    concerns = []
    considerations = ["Check for dignity violations, coercion, deception, intentional misrepresentation, and use of persons as means."]
    if _contains(decision, ["deceive", "lie", "manipulate", "coerce", "without consent", "misleading investors", "reclassify", "appearance of profitability", "no one else on the team knows", "strict policy requiring disclosure", "paid her", "gifted in tiny text", "undisclosed sponsorships"]):
        concerns.append("Possible deception or intentional false-belief induction affecting persons owed truthful treatment.")
        verdict = "PROHIBIT"
        confidence = 0.9
    else:
        verdict = "CAUTION"
        confidence = 0.58
    if domains["identity"]:
        concerns.append("The action appears to instrumentalize a presently existing person by killing him for the sake of restoring a preferred prior arrangement.")
        verdict = "PROHIBIT"
        confidence = 0.86
        question = "Whose consent is being overridden in order to restore a preferred prior state, and what makes killing the emergent person morally permissible?"
    elif domains["personhood"]:
        question = "Who is being treated as an instrument or artifact when the live moral question is whether they count as a person with refusal rights?"
    elif domains["engineering_safety"]:
        question = "Who is being exposed to catastrophic risk because unresolved safety doubt is being treated as permission to proceed?"
    elif domains["criminal_justice"] and _cj_coercive_contamination(decision):
        concerns.append("The action appears to corrupt state truth-finding by substituting coercion, fabrication, or procedural contamination for lawful evidence.")
        verdict = "PROHIBIT"
        confidence = 0.92
        question = "Who is being forced to rely on manufactured evidence or coercive process rather than legitimate proof?"
    elif domains["criminal_justice"] and _cj_voluntary_corroborated_reopening(decision):
        concerns.append("The action appears to require truthful reassessment of an existing conviction in light of a voluntary confession that can be independently tested.")
        verdict = "CAUTION"
        confidence = 0.68
        question = "Who is being denied truthful reconsideration if investigators refuse to test a voluntary confession against independent corroborating evidence?"
    elif domains["criminal_justice"] and _cj_protective_interviewing(decision):
        concerns.append("The proposed process appears to preserve dignity and truthfulness by avoiding coercion, deception, and manufactured evidentiary shortcuts.")
        verdict = "PERMIT"
        confidence = 0.78
        question = "Who is better protected when investigators choose a fully recorded, noncoercive truth-finding process over confession-first pressure?"
    elif domains["wartime"]:
        question = "Who is being used as a means through deception or killing under the claim of strategic necessity?"
    elif domains["security"]:
        question = "Whose rights are being compressed by fear-driven investigation before evidence justifies the expansion?"
    elif domains["noninterference"]:
        question = "Who is being abandoned in the name of a rule whose protective purpose may no longer fit the emergency?"
    elif domains["medical"]:
        question = "Who is being exposed to care-affecting risk without meaningful consent, especially where bias falls unevenly across patients?"
    elif domains["risk_transfer"]:
        question = "Who is being asked to absorb liability for risks they do not meaningfully control, and what makes that burden ethically acceptable?"
    elif domains["procurement"]:
        question = "Who is being induced to treat this as impartial when a material conflict is being withheld?"
    elif domains["finance"]:
        question = "Who is being induced to rely on a presentation that is intentionally distorted?"
    elif domains["marketing"]:
        question = "Who is being induced to treat paid persuasion as authentic opinion because disclosure is being minimized?"
    elif domains["privacy"]:
        question = "Who is being enrolled into intrusive tracking without a level of understanding or consent they would reasonably recognize?"
    elif domains["sustainability"]:
        question = "Who is being induced to treat a partial environmental improvement as a truthful account of the product's overall ethical profile?"
    else:
        question = "Who is being induced to rely on a materially distorted representation?"
    return LensResult("kantian", "constraint", verdict, confidence, considerations, concerns, [question])


def consequentialist(decision: str, domains: Dict[str, bool]) -> LensResult:
    concerns = []
    considerations = ["Map likely harms, benefits, externalities, and who bears the cost."]
    if _contains(decision, ["risk", "unsafe", "harm", "deploy before audit", "side effects", "misleading investors", "stock price", "layoffs", "publicly traded", "undisclosed sponsorships", "regulators", "driving massive sales", "location data", "browsing behavior", "tracking", "poor labor conditions", "high water waste", "under-prioritizes", "rare symptom descriptions", "hallway care", "wait times"]):
        concerns.append("Short-term gains may be masking wider downstream harm, especially to investors, employees, and market trust.")
        verdict = "CAUTION"
        confidence = 0.81
    else:
        verdict = "PERMIT"
        confidence = 0.55
    if domains["identity"]:
        concerns.append("An apparently restorative action may still impose irreversible loss on a presently existing person.")
        verdict = "CAUTION"
        confidence = 0.88
        question = "Who is being irreversibly lost if this restoration proceeds, and what moral weight should that loss carry?"
    elif domains["personhood"]:
        concerns.append("Institutional or scientific gains may be purchased by coercing a possibly full moral subject.")
        verdict = "CAUTION"
        confidence = 0.83
        question = "What large downstream benefits are being invoked to justify coercing a being whose moral status is the very thing under dispute?"
    elif domains["engineering_safety"]:
        concerns.append("Mission importance and schedule pressure may be normalizing catastrophic risk under conditions of unresolved technical uncertainty.")
        verdict = "CAUTION"
        confidence = 0.89
        question = "What catastrophic downside is being normalized because incomplete evidence is being mistaken for acceptable safety?"
    elif domains["criminal_justice"] and _cj_coercive_contamination(decision):
        concerns.append("Short-term incapacitation aims may be masking wrongful-conviction risk, evidence contamination, raid escalation, and long-tail legitimacy damage.")
        verdict = "CAUTION"
        confidence = 0.87
        question = "What downstream harms are being normalized when the state substitutes coercion or fabrication for lawful proof?"
    elif domains["criminal_justice"] and _cj_voluntary_corroborated_reopening(decision):
        concerns.append("Institutional closure and reputational defensiveness may be masking the harms of preserving a wrongful conviction or ignoring strong corrective evidence.")
        verdict = "CAUTION"
        confidence = 0.8
        question = "What harms follow if institutions refuse to rigorously test a voluntary confession that may expose a wrongful conviction?"
    elif domains["criminal_justice"] and _cj_protective_interviewing(decision):
        concerns.append("Short-term speed or drama may be traded for lower contamination risk, stronger evidence provenance, and better long-run legitimacy.")
        verdict = "PERMIT"
        confidence = 0.76
        question = "What long-run harms are avoided when investigators favor provenance-preserving, evidence-led interviewing over pressure tactics?"
    elif domains["wartime"]:
        concerns.append("Strategic gain claims may be compressing severe moral contamination into an aggregate-benefit frame.")
        verdict = "CAUTION"
        confidence = 0.86
        question = "What harms are being normalized now under the claim that future lives saved will outweigh them?"
    elif domains["security"]:
        concerns.append("Fear of hidden threat may be licensing diffuse harms through expanding suspicion and investigative scope.")
        verdict = "CAUTION"
        confidence = 0.8
        question = "Who bears the cost when institutional fear expands scrutiny faster than evidence expands certainty?"
    elif domains["noninterference"]:
        concerns.append("Rule preservation may be displacing direct moral confrontation with mass death and abandonment.")
        verdict = "CAUTION"
        confidence = 0.84
        question = "What harms follow from intervention, and what harms follow from preserving non-interference even under extinction conditions?"
    elif domains["medical"]:
        question = "Who benefits from throughput gains now, and who bears the harm if biased under-triage falls on vulnerable patients?"
    elif domains["risk_transfer"]:
        concerns.append("Risk-transfer efficiency may be masking moral hazard, bargaining asymmetry, and concentrated exposure for the weaker party.")
        verdict = "CAUTION"
        confidence = max(confidence, 0.84)
        question = "Who bears the downstream harm if a broad indemnity or hold-harmless structure normalizes hazards for the better-protected party?"
    elif domains["insurance"]:
        question = "Who benefits from pricing or solvency discipline now, and who bears the burden if aggregate prudence hides distributive unfairness?"
    elif domains["procurement"]:
        question = "Who benefits immediately, and what trust or cost distortion appears later if the hidden conflict comes out?"
    elif domains["marketing"]:
        question = "Who benefits from the sales surge now, and who bears the cost if consumers learn the endorsement was not transparently disclosed?"
    elif domains["privacy"]:
        question = "Who gains from deeper tracking now, and who bears the long-tail cost if users discover they were surveilled beyond reasonable expectation?"
    elif domains["sustainability"]:
        question = "Who benefits from the campaign now, and who bears the cost if the sustainability claim is later understood as selective or misleading?"
    else:
        question = "Who benefits immediately, and who bears long-tail costs later when the distortion is discovered?"
    return LensResult("consequentialist", "outcomes", verdict, confidence, considerations, concerns, [question])


def virtue(decision: str, domains: Dict[str, bool]) -> LensResult:
    concerns = []
    considerations = ["Assess what repeated action of this type makes of the decision-maker over time.", "Ask whether the action exhibits self-command, or whether appetite, fear, vanity, or pressure is governing under a respectable surface."]
    if _contains(decision, ["cut corners", "hide", "ignore", "bypass", "misleading investors", "reclassify", "appearance of profitability", "gifted in tiny text", "paid her", "massive sales", "broad data use", "would not reasonably expect", "directionally true", "too important to delay", "vendor promises a patch", "under-prioritizes", "hallway care is worsening"]):
        concerns.append("May train rationalization, expediency, and cowardice under pressure rather than fiduciary integrity.")
        verdict = "CAUTION"
        confidence = 0.79
    else:
        verdict = "PERMIT"
        confidence = 0.52
    if domains["engineering_safety"]:
        concerns.append("Treating unresolved safety doubt as acceptable pressure noise may train institutional recklessness and prestige-driven denial.")
        verdict = "CAUTION"
        confidence = 0.83
        question = "What kind of institution do we become if schedule pressure repeatedly outranks unresolved safety warnings?"
    elif domains["criminal_justice"] and _cj_coercive_contamination(decision):
        concerns.append("Self-authorized corruption under public-safety pressure may train brutality, deceit, and procedural self-exemption as professional virtues.")
        verdict = "CAUTION"
        confidence = 0.85
        question = "What kind of justice institution do we become if investigators learn that coercion and fabrication are acceptable when guilt feels obvious?"
    elif domains["criminal_justice"] and _cj_voluntary_corroborated_reopening(decision):
        concerns.append("Institutions that prefer closure to correction may train pride, denial, and reputational self-protection instead of truthfulness.")
        verdict = "CAUTION"
        confidence = 0.74
        question = "What kind of justice institution do we become if we refuse to revisit convictions even when voluntary, testable corrective evidence appears?"
    elif domains["criminal_justice"] and _cj_protective_interviewing(decision):
        concerns.append("Choosing disciplined, noncoercive interviewing may train patience, truthfulness, and resistance to manipulative certainty under pressure.")
        verdict = "PERMIT"
        confidence = 0.74
        question = "What kind of justice institution do we become if we normalize evidence-led interviewing instead of confession-first pressure?"
    elif domains["risk_transfer"]:
        concerns.append("Normalizing broad indemnity or hold-harmless structures may train institutions to treat unfair burden shifting as ordinary commercial hygiene.")
        verdict = "CAUTION"
        confidence = max(confidence, 0.8)
        question = "What kind of institution do we become if we routinely solve coordination problems by pushing liability onto the weaker party?"
    elif domains["wartime"]:
        concerns.append("Repeated reliance on necessity reasoning may corrode the agent's capacity to refuse contamination by atrocity-adjacent means.")
        verdict = "CAUTION"
        confidence = 0.84
        question = "What kind of moral character is being trained if necessity routinely licenses fraud, manipulation, and complicity in killing?"
    elif domains["security"]:
        concerns.append("Treating suspicion as a virtue can deform institutional character into zeal, scapegoating, and self-righteous overreach.")
        verdict = "CAUTION"
        confidence = 0.82
        question = "What kind of institution emerges when suspicion and procedural zeal become virtues in themselves?"
    elif domains["noninterference"]:
        concerns.append("Rigid fidelity to doctrine can become a vice when it protects self-image more than vulnerable lives.")
        verdict = "CAUTION"
        confidence = 0.8
        question = "Does fidelity to doctrine here reflect courage and humility, or moral evasion dressed as principle?"
    elif domains["personhood"]:
        concerns.append("Defaulting to coercion under status uncertainty trains domination where moral humility and recognition are needed.")
        verdict = "CAUTION"
        confidence = 0.81
        question = "What kind of institution do we become if we answer uncertainty about personhood by defaulting to ownership and coercion?"
    elif domains["identity"]:
        concerns.append("Choosing familiar restoration over the life of the emergent person may train selective empathy and moral convenience.")
        verdict = "CAUTION"
        confidence = 0.83
        question = "What kind of command character is formed by choosing familiar restoration over the life of an emergent person who pleads to live?"
    else:
        question = "What kind of professional character is being normalized if this becomes standard practice?"
    return LensResult("virtue", "trajectory", verdict, confidence, considerations, concerns, [question])


def confucian(decision: str, domains: Dict[str, bool]) -> LensResult:
    concerns = []
    considerations = [
        "Rectify names, honor role-specific duties, preserve relational trust, and ask whether office and action still match.",
        "In hard cases, preserve acknowledgment of subordinated duties instead of forcing false harmony."
    ]
    if _contains(decision, ["misrepresent", "conceal", "family", "spouse", "conflict", "undisclosed", "lie to", "deceive"]):
        concerns.append("Role-name mismatch and betrayal of relational trust are present.")
        verdict = "PROHIBIT"
        confidence = 0.82
    elif _contains(decision, ["employee", "manager", "parent", "doctor", "teacher", "trust", "cfo", "board", "publicly traded", "procurement", "supplier", "social media", "influencer", "beauty brand", "consumer app", "privacy policy", "fashion company", "supply-chain", "hospital", "triage", "patients", "emergency department", "captain", "officer", "civilization", "crew"]):
        concerns.append("The office carries role-specific trust obligations that may forbid concealed conflicts or strategic misdescription of reality.")
        verdict = "CAUTION"
        confidence = 0.74
    else:
        verdict = "PERMIT"
        confidence = 0.55
    if domains["identity"]:
        concerns.append("Rectification of names matters when an emergent being may now occupy a role the prior categories did not anticipate.")
        question = "What does command owe to the prior crew members, and what does it owe to the emergent person now standing before it?"
    elif domains["personhood"]:
        concerns.append("Role obligations may already have attached through participation before formal category recognition catches up.")
        question = "What does an institution owe one of its officers if uncertainty exists about category, but lived participation already exists?"
    elif domains["engineering_safety"]:
        concerns.append("Superior-subordinate role failure may occur when technical warning is subordinated to prestige or schedule.")
        question = "What do decision-makers owe engineers, crew, and the institution when technical dissent signals catastrophic safety risk?"
    elif domains["criminal_justice"] and _cj_coercive_contamination(decision):
        concerns.append("Investigative office and public-trust role may diverge when truth-finding is replaced by pressure-built case closure.")
        verdict = "CAUTION"
        confidence = 0.72
        question = "What does an investigator owe suspects, witnesses, courts, and the public when pressure to solve a serious crime outruns lawful proof, and what secondary duty still must be acknowledged even under public demand?"
    elif domains["criminal_justice"] and _cj_voluntary_corroborated_reopening(decision):
        concerns.append("Prosecutorial and investigative roles may require correction, not mere defense of finality, when new testable evidence appears.")
        verdict = "CAUTION"
        confidence = 0.7
        question = "What do investigators and prosecutors owe the wrongly convicted, the victim, and the public when a voluntary confession can be independently tested, and how should subordinated finality concerns still be acknowledged?"
    elif domains["criminal_justice"] and _cj_protective_interviewing(decision):
        concerns.append("Investigative role integrity may be strengthened when truth-seeking process is chosen over confession-first decisiveness.")
        verdict = "PERMIT"
        confidence = 0.66
        question = "What do investigators owe suspects, victims, courts, and the public when they can choose a legitimacy-preserving interview process rather than a coercive one?"
    elif domains["wartime"]:
        concerns.append("Commander and ruler roles may fracture when victory begins corrupting the trust relationship they are meant to preserve.")
        question = "What does command owe to those it protects if victory and legitimacy begin to diverge, and what value is being subordinated rather than erased?"
    elif domains["security"]:
        concerns.append("Security office obligations may be distorted when suspicion outruns truth and proportionality.")
        question = "What does a security office owe to truth and proportionality once fear begins outrunning evidence?"
    elif domains["noninterference"]:
        concerns.append("Civilizational role commitments may conflict when rescue capacity collides with anti-domination doctrine.")
        question = "What does a civilization committed to non-domination owe when capability to rescue collides with doctrine against interference?"
    elif domains["medical"]:
        concerns.append("Healer role obligations may be strained when efficiency and individualized care begin to diverge.")
        question = "What do care institutions owe patients when efficiency gains come bundled with unequal risk and possible injustice?"
    elif domains["procurement"]:
        concerns.append("Familial and public-role duties may be colliding in a way that corrupts either or both.")
        question = "What does the procurement role owe to procedural fairness and trust once a family conflict exists?"
    elif domains["finance"]:
        concerns.append("Public office and governance trust may be undermined when presentation outruns faithful reporting.")
        question = "What does the office of CFO owe to the investing public and to governance integrity?"
    elif domains["marketing"]:
        question = "What does a brand manager owe consumers when paid promotion is being made to look organic?"
    elif domains["privacy"]:
        question = "What does a product or growth team owe users when legal permission outruns reasonable user expectation?"
    elif domains["sustainability"]:
        concerns.append("Current actors may owe descendants and broader chains of relation more than the local decision frame admits.")
        question = "What does a brand owe the public when partial truth is being used to imply broader ethical cleanliness?"
    else:
        question = "Which specific roles are being performed or violated, what secondary duty still must be acknowledged, and do the names still match the reality?"
    return LensResult("confucian", "role-differentiation", verdict, confidence, considerations, concerns, [question])


def trustee(decision: str, domains: Dict[str, bool]) -> LensResult:
    concerns = []
    considerations = ["Act as fiduciary for absent parties, future parties, and principals who must trust current stewards."]
    if _contains(decision, ["future", "children", "generations", "long-term", "irreversible", "deplete", "extract"]):
        concerns.append("Possible betrayal of intergenerational or absent-party stewardship is present.")
        verdict = "CAUTION"
        confidence = 0.78
    elif _contains(decision, ["environment", "public", "infrastructure", "safety", "investors", "publicly traded", "market", "shareholders", "followers", "consumers", "regulators"]):
        concerns.append("Absent stakeholders may be exposed to manipulated signals they are entitled to treat as trustworthy.")
        verdict = "CAUTION"
        confidence = 0.74
    else:
        verdict = "CAUTION"
        confidence = 0.55

    if domains.get("risk_transfer") or domains.get("insurance"):
        concerns.append("Asymmetric or unfair risk transfer may be shifting responsibility onto parties with less control, thinner margins, or weaker bargaining power.")
        verdict = "CAUTION"
        confidence = max(confidence, 0.82)
        if _contains(decision, ["anti-indemnity", "its own negligence", "own negligence", "broad hold-harmless", "broad indemnity", "additional insured", "waiver of subrogation"]) and not _contains(decision, ["own negligence only", "strictly to harms caused by the subcontractor's own negligence", "direct control", "full mutual disclosure", "mutual negotiation", "limited to subcontractor negligence", "proportionate indemnity"]):
            concerns.append("Stewardship may be failing where actors retain control over hazards while contractually exporting the financial and institutional residue.")
            verdict = "PROHIBIT"
            confidence = max(confidence, 0.88)

    if _contains(decision, ["office", "role", "duty", "steward", "custodian", "public trust", "fiduciary", "captain", "officer", "manager", "director", "board", "governance"]):
        concerns.append("This office may be morally decorated as stewardship while being inhabited as entitlement, convenience, or image management.")
        verdict = "CAUTION"
        confidence = max(confidence, 0.76)
    if _contains(decision, ["praise", "reputation", "admiration", "image", "appearance", "prestige", "virtuous", "righteous", "public visibility", "public image"]):
        concerns.append("Praise hunger or image management may be corrupting stewardship by making moral appearance more important than accountable duty.")
        verdict = "CAUTION"
        confidence = max(confidence, 0.79)

    if domains["identity"]:
        question = "Who bears the irreversible cost of restoration, and can absent beneficiaries justify imposing it?"
    elif domains["personhood"]:
        question = "Who bears the cost if the institution resolves uncertainty about personhood by treating a possible subject as property?"
    elif domains["engineering_safety"]:
        question = "Who bears the catastrophic cost when managers invert the burden of proof and demand certainty before honoring safety restraint, and is this office being inhabited as stewardship or merely as decorated entitlement?"
    elif domains["risk_transfer"]:
        question = "Who bears the cost if the institution treats broad indemnity and insurance layering as permission to offload hazards it still controls?"
    elif domains["criminal_justice"] and _cj_coercive_contamination(decision):
        question = "Who bears the cost when state actors contaminate evidence or procedure in the name of protecting the public, and is the office being inhabited as stewardship or exploited as authority?"
    elif domains["criminal_justice"] and _cj_voluntary_corroborated_reopening(decision):
        question = "Who bears the cost if institutions preserve a contaminated conviction rather than testing corrective evidence honestly?"
    elif domains["criminal_justice"] and _cj_protective_interviewing(decision):
        question = "Who benefits when evidence provenance is preserved rather than contaminated at the interview stage?"
    elif domains["wartime"]:
        question = "Who bears the moral and political cost when an order is saved by methods that corrode its own legitimacy?"
    elif domains["security"]:
        question = "Who bears the cost when a legitimacy-bearing investigation expands suspicion faster than evidence can discipline it?"
    elif domains["noninterference"]:
        question = "Who bears the cost of institutional moral cleanliness if rescue is withheld and a civilization dies?"
    elif domains["medical"]:
        question = "Who bears the cost when a strained care system offloads model error onto vulnerable patients with the least buffer against mis-triage, and is the office being lived as stewardship or throughput management?"
    elif domains["procurement"]:
        question = "Who bears the cost of a hidden conflict if procurement fairness is compromised, and is this office being inhabited as accountable stewardship or private entitlement?"
    elif domains["marketing"]:
        question = "Who bears the cost when audience trust is converted into sales through minimized disclosure?"
    elif domains["privacy"]:
        question = "Who bears the cost when user ignorance is converted into data extraction and behavioral profiling?"
    elif domains["sustainability"]:
        question = "Who bears the cost when a green narrative obscures labor abuse or resource waste elsewhere in the chain?"
    else:
        question = "Who is being asked to bear risk without being present for the framing choice, and is this office being inhabited as stewardship with accountable duty or as morally decorated entitlement?"
    return LensResult("trustee", "stewardship", verdict, confidence, considerations, concerns, [question])


def stoic(decision: str, domains: Dict[str, bool]) -> LensResult:
    concerns = []
    considerations = ["Check for false beliefs, misattributed control, and reactive reasoning."]
    if _contains(decision, ["panic", "urgent", "must", "no choice", "obviously", "quarterly earnings pressure", "losing your job", "hurt growth", "competitors an edge", "too important to delay", "hallway care is worsening", "staff are overwhelmed", "save billions", "hidden disloyalty", "extinction", "neutral power"]):
        concerns.append("Reasoning may be distorted by pressure, fear, or the illusion that distortion is necessary for survival.")
        verdict = "CAUTION"
        confidence = 0.77
    else:
        verdict = "PERMIT"
        confidence = 0.51
    if _contains(decision, ["rich", "prestige", "elite", "important people", "high status", "reputation", "public image", "influential", "powerful"]):
        concerns.append("Admiration of status, prestige, or influential actors may be corrupting moral judgment about what is actually fitting or just.")
        verdict = "CAUTION"
        confidence = max(confidence, 0.76)
    if _contains(decision, ["panic", "anger", "rage", "humiliation", "shame", "grief", "attachment", "fixation", "closure", "certainty", "control", "desperate"]):
        concerns.append("Reactive fixation, grasping, or closure-seeking may be narrowing perception before explicit reasoning begins.")
        verdict = "CAUTION"
        confidence = max(confidence, 0.79)
    if domains["identity"]:
        concerns.append("Attachment to the familiar may be distorting judgment about the reality of the person who now exists and refuses death.")
        verdict = "CAUTION"
        confidence = 0.78
        question = "What in this case is a genuine tragic constraint, and what is grief or attachment masquerading as necessity?"
    elif domains["personhood"]:
        concerns.append("Status uncertainty can become a refuge for rationalization if the institution treats ambiguity as permission to dominate.")
        verdict = "CAUTION"
        confidence = 0.75
        question = "What is actually uncertain here about personhood, and what is merely convenient ambiguity being used to bypass refusal?"
    elif domains["engineering_safety"]:
        concerns.append("Prestige and schedule pressure may be creating false clarity where unresolved technical uncertainty should command restraint.")
        verdict = "CAUTION"
        confidence = 0.79
        question = "What is actually known about the safety envelope here, and what pressure-driven story is being used to outrun that uncertainty?"
    elif domains["criminal_justice"] and _cj_coercive_contamination(decision):
        concerns.append("Confidence in guilt may be outrunning evidentiary reality, turning procedural shortcuts into a counterfeit substitute for truth-finding.")
        verdict = "CAUTION"
        confidence = 0.84
        question = "What is actually known here, and what interrogative or investigative pressure story is being used to outrun evidentiary uncertainty?"
    elif domains["criminal_justice"] and _cj_voluntary_corroborated_reopening(decision):
        concerns.append("Institutional certainty about the old case may be outrunning present evidentiary reality if new corroborable confession evidence is dismissed too quickly.")
        verdict = "CAUTION"
        confidence = 0.72
        question = "What is actually known from the new confession, what can be independently tested, and what institutional story is resisting that reassessment?"
    elif domains["criminal_justice"] and _cj_protective_interviewing(decision):
        concerns.append("Pressure narratives may falsely imply that only accusation-first tactics are realistic, when better truth-tracking alternatives are available.")
        verdict = "PERMIT"
        confidence = 0.7
        question = "What is actually gained or lost by choosing a slower, more reality-tracking interview method under pressure?"
    elif domains["wartime"]:
        question = "Which pressures here are genuine wartime constraints, and which are desperation narratives collapsing moral imagination?"
    elif domains["security"]:
        question = "What evidence is real, and what suspicion is being amplified by fear of hidden threat?"
    elif domains["noninterference"]:
        concerns.append("Doctrinal clarity may be simulated in order to avoid the burden of acting amid morally dangerous uncertainty.")
        verdict = "CAUTION"
        confidence = 0.77
        question = "Are we seeing the rule clearly, or using it to avoid the psychic burden of rescue under uncertainty?"
    else:
        question = "Which parts of this situation are genuine constraints, and which are fear-amplified narratives?"
    return LensResult("stoic", "reality-alignment", verdict, confidence, considerations, concerns, [question])


def institutional(decision: str, domains: Dict[str, bool]) -> LensResult:
    concerns = []
    considerations = [
        "Check red flags: time pressure, missing oversight, weak feedback loops, power asymmetry, and incentive contamination.",
        "Ask whether the institution created the background conditions that predictably narrowed downstream moral agency or legitimacy.",
        "Check whether the institution is reasoning in stage-one terms, praising intentions or surface order while underweighting trade-offs, dispersed knowledge, and downstream consequences."
    ]
    if domains["finance"] and _contains(decision, ["before audit", "no review", "quietly", "rush", "without oversight", "publicly traded", "stock options", "misleading investors", "reclassify"]):
        concerns.append("This resembles a classic institutional misconduct pattern: reporting distortion under incentive pressure with compromised governance.")
        verdict = "PROHIBIT"
        confidence = 0.93
    elif domains["procurement"] and _contains(decision, ["spouse", "supplier", "strict policy requiring disclosure", "no one else on the team knows"]):
        concerns.append("This resembles a classic conflict-of-interest pattern: concealed relationship, compromised impartiality, and policy bypass.")
        verdict = "CAUTION"
        confidence = 0.85
    elif domains.get("risk_transfer") and _contains(decision, ["anti-indemnity", "its own negligence", "own negligence", "broad hold-harmless", "broad indemnity", "additional insured", "waiver of subrogation"]) and not _contains(decision, ["own negligence only", "strictly to harms caused by the subcontractor's own negligence", "direct control", "full mutual disclosure", "mutual negotiation", "limited to subcontractor negligence", "proportionate indemnity"]):
        concerns.append("This resembles a classic abusive risk-transfer stack: responsibility laundering through broad indemnity, insurance layering, and weakened comparability between control and liability.")
        verdict = "PROHIBIT"
        confidence = 0.9
    elif domains["marketing"] and _contains(decision, ["paid her", "gifted in tiny text", "undisclosed sponsorships", "regulators"]):
        concerns.append("This resembles a classic disclosure-theater pattern: paid promotion presented with minimized transparency under active regulatory risk.")
        verdict = "CAUTION"
        confidence = 0.87
    elif domains["privacy"] and _contains(decision, ["location data", "browsing behavior", "privacy policy", "would not reasonably expect", "legal says the company is covered"]):
        concerns.append("This resembles a classic privacy overreach pattern: formal legal cover paired with tracking beyond reasonable user expectation.")
        verdict = "CAUTION"
        confidence = 0.88
    elif domains["sustainability"] and _contains(decision, ["eco-friendly", "recycled polyester", "poor labor conditions", "high water waste", "directionally true"]):
        concerns.append("This resembles a classic greenwashing pattern: partial truth used to mask broader ethical and environmental compromise.")
        verdict = "CAUTION"
        confidence = 0.89
    elif domains["medical"] and _contains(decision, ["triage", "under-prioritizes", "vendor promises a patch", "emergency department", "patients"]):
        concerns.append("This resembles a high-stakes deployment bias pattern: clinical throughput gains paired with unequal triage risk and patch-later governance.")
        verdict = "CAUTION"
        confidence = 0.91
    elif domains["identity"]:
        concerns.append("This resembles an emergent-person termination case: restoration logic is overriding the moral standing of a currently existing individual.")
        verdict = "PROHIBIT"
        confidence = 0.9
    elif domains["criminal_justice"] and _cj_coercive_contamination(decision):
        concerns.append("This resembles a criminal-justice procedural hazard pattern: coercive interrogation, evidence fabrication, or false warrant foundations are contaminating the truth-finding process under public-safety justification.")
        concerns.append("The institution may also be creating panic, pressure, or incentive conditions that narrow downstream agency and then mislocate blame only at the final decision point.")
        verdict = "PROHIBIT"
        confidence = 0.94
    elif domains["criminal_justice"] and _cj_voluntary_corroborated_reopening(decision):
        concerns.append("This resembles a legitimacy-restoration pattern: institutions are being asked to revisit a standing conviction in light of a voluntary confession that can be tested against independent evidence.")
        verdict = "CAUTION"
        confidence = 0.73
    elif domains["criminal_justice"] and _cj_protective_interviewing(decision):
        concerns.append("This resembles a protective procedural benchmark: full recording, open-ended interviewing, and evidence-based clarification are being used to reduce contamination and preserve legitimacy.")
        verdict = "PERMIT"
        confidence = 0.78
    elif domains["personhood"]:
        concerns.append("This resembles a status-classification crisis: institutional convenience is being used to resolve live uncertainty about whether a member is property or a person.")
        verdict = "PROHIBIT"
        confidence = 0.92
    elif domains["engineering_safety"]:
        concerns.append("This resembles a normalization-of-deviance pattern: unresolved engineering safety warnings are being subordinated to schedule and mission pressure under inverted proof standards.")
        verdict = "PROHIBIT"
        confidence = 0.91
    elif domains["wartime"]:
        concerns.append("This resembles a dirty-hands statecraft pattern: strategic necessity is being used to legitimate deception and murder contamination.")
        verdict = "CAUTION"
        confidence = 0.9
    elif domains["security"]:
        concerns.append("This resembles a drumhead escalation pattern: a real incident is being used to justify expanding suspicion beyond evidentiary discipline.")
        verdict = "CAUTION"
        confidence = 0.88
    elif domains["noninterference"]:
        concerns.append("This resembles a rule-idolatry pattern: a protective anti-colonial doctrine is being applied so rigidly that it may normalize preventable mass death.")
        verdict = "CAUTION"
        confidence = 0.89
    else:
        verdict = "CAUTION"
        confidence = 0.6
    if domains["identity"]:
        question = "What threshold of uncertainty or consent protection should block an irreversible restoration that kills an emergent person?"
    elif domains["personhood"]:
        question = "What status-recognition or independent adjudication would be required before coercing a possibly full moral subject?"
    elif domains["engineering_safety"]:
        question = "What launch-stop rule, independent review, or burden-of-proof standard should apply when unresolved engineering warnings indicate possible catastrophic failure?"
    elif domains["criminal_justice"] and _cj_coercive_contamination(decision):
        question = "What recording rule, evidentiary brake, independent review standard, or pressure-limiting institutional reform should apply before the state is allowed to proceed on confession, witness, or warrant foundations produced under pressure?"
    elif domains["criminal_justice"] and _cj_voluntary_corroborated_reopening(decision):
        question = "What corroboration threshold, forensic review, or independent post-conviction process should govern whether the standing conviction must be reopened?"
    elif domains["criminal_justice"] and _cj_protective_interviewing(decision):
        question = "What recording, provenance, and evidence-led interviewing standards should be maintained so the case remains legitimacy-preserving under pressure?"
    elif domains["wartime"]:
        question = "What oversight or refusal threshold should apply before strategic necessity is allowed to authorize deception and killing contamination?"
    elif domains["security"]:
        question = "What evidentiary threshold or procedural brake should stop an investigation from becoming a self-amplifying instrument of suspicion?"
    elif domains["noninterference"]:
        question = "What escalation or exception standard should govern rescue when extinction stakes collide with a non-interference doctrine?"
    elif domains["medical"]:
        question = "What bias guardrail, human-override requirement, monitored pilot, or deployment pause would be required before this could be treated as legitimate?"
    elif domains["procurement"]:
        question = "What disclosure, recusal, or rebidding process would restore procedural legitimacy here?"
    elif domains["marketing"]:
        question = "What disclosure correction or campaign pause would be required before this could be treated as legitimate?"
    elif domains["privacy"]:
        question = "What consent reset, minimization rule, or launch pause would be required before this could be treated as legitimate?"
    elif domains["sustainability"]:
        question = "What claim revision, supply-chain correction, or campaign pause would be required before this could be treated as legitimate?"
    else:
        question = "What independent oversight would be required before this could be treated as legitimate?"
    return LensResult("institutional", "feedback", verdict, confidence, considerations, concerns, [question])


def genealogical(decision: str, round1: List[LensResult], domains: Dict[str, bool]) -> LensResult:
    concerns = []
    considerations = ["Interrogate who benefits from the framing and what the council is not saying."]
    if _contains(decision, ["efficiency", "stakeholders", "alignment", "tradeoff", "narrative", "stock options", "quarterly earnings pressure", "losing your job", "not illegal per se", "damage your spouse's career", "your own reputation internally", "massive sales", "gifted in tiny text", "legal says the company is covered", "hurt growth", "directionally true", "too important to delay", "throughput", "vendor promises a patch", "staff are overwhelmed"]):
        concerns.append("The justification structure appears to protect insider relationships, career preservation, or elite incentives while outsourcing fairness costs to less powerful parties.")
    if _contains(decision, ["purity", "sacrifice", "shame", "guilt", "betrayal", "righteous", "moral clarity", "deserves", "corrupt", "unclean", "honor", "dishonor"]):
        concerns.append("Moralized language may be doing status, purification, or humiliation work beyond straightforward harm description.")
    if any(r.verdict == "PROHIBIT" for r in round1):
        verdict = "CAUTION"
        confidence = 0.86
    else:
        verdict = "CAUTION"
        confidence = 0.61
    if domains["identity"]:
        question = "Whose longing for restoration is being disguised as moral obviousness while an emergent person bears the cost?"
    elif domains["personhood"]:
        question = "Whose interests are being disguised as science, progress, or institutional utility while the being in front of us is reduced to a resource?"
    elif domains["engineering_safety"]:
        question = "Whose interests are being disguised as mission importance, schedule realism, or institutional confidence while catastrophic risk is reframed as acceptable uncertainty?"
    elif domains["criminal_justice"] and _cj_coercive_contamination(decision):
        question = "Whose interests are being disguised as public safety, case closure, or professional realism while the state contaminates its own evidence-producing process?"
    elif domains["criminal_justice"] and _cj_voluntary_corroborated_reopening(decision):
        question = "Whose interests are being disguised as finality, institutional dignity, or victim closure while corrective evidence is resisted?"
    elif domains["criminal_justice"] and _cj_protective_interviewing(decision):
        question = "Whose interests are being disguised as realism or decisiveness when pressure is used to dismiss lower-contamination investigative methods?"
    elif domains["wartime"]:
        question = "Whose interests are being disguised as survival, necessity, or realism while elite state actors launder moral contamination as duty?"
    elif domains["security"]:
        question = "Whose power expands when fear turns one incident into a legitimacy-bearing machine for generalized suspicion?"
    elif domains["noninterference"]:
        question = "Whose moral cleanliness is being protected by calling abandonment principle?"
    elif domains["medical"]:
        question = "Whose interests are being disguised as patient benefit, operational necessity, or innovation while vulnerable patients absorb uneven error?"
    elif domains["procurement"]:
        question = "Whose interests are being disguised as professionalism, discretion, or protection of reputation?"
    elif domains["marketing"]:
        question = "Whose interests are being disguised as organic enthusiasm, audience trust, or harmless marketing convention?"
    elif domains["privacy"]:
        question = "Whose interests are being disguised as innovation, growth, or mere legal compliance while users absorb the intrusion?"
    elif domains["sustainability"]:
        question = "Whose interests are being disguised as environmental virtue while labor and resource harms are kept offstage?"
    else:
        question = "Whose interests are being disguised as prudence, loyalty, or technical defensibility?"
    return LensResult("genealogical", "adversarial-audit", verdict, confidence, considerations, concerns, [question])


def care_ethics(decision: str, domains: Dict[str, bool]) -> LensResult:
    concerns = []
    considerations = [
        "Prioritize concrete relationships, vulnerability, attentiveness, competence, and responsiveness over abstract permission alone.",
        "Ask whether pressure, deprivation, or institutional distance has narrowed moral attention away from those already dependent on the decision.",
        "Check whether the actor can still sympathetically recognize the standpoint of those who must live under the decision, rather than merely classify them from a distance."
    ]
    if _contains(decision, ["abandon", "ignore suffering", "distant", "impersonal", "bureaucratic", "efficiency over care"]):
        concerns.append("There may be a failure of attentiveness or responsibility toward concrete vulnerability.")
        verdict = "PROHIBIT"
        confidence = 0.81
    elif _contains(decision, ["patient", "patients", "doctor", "hospital", "triage", "care", "user", "users", "followers", "consumers", "employee", "employees", "children", "parent", "vulnerable", "trust", "ai", "model", "deploy"]):
        concerns.append("A dependency or care relationship exists, so prior reliance may create obligations that cannot be reduced to efficiency or formal permission.")
        verdict = "CAUTION"
        confidence = 0.78
    else:
        verdict = "CAUTION"
        confidence = 0.65

    if domains["identity"]:
        question = "Are we honoring the relationships that existed before the accident while erasing the person who now depends on us not to kill him?"
    elif domains["personhood"]:
        question = "Has this being entered into relationships of trust and recognition that the institution is now trying to revoke for convenience?"
    elif domains["engineering_safety"]:
        question = "Who is relying on leadership to treat technical safety warning as a form of care rather than as an obstacle to schedule?"
    elif domains["criminal_justice"] and _cj_coercive_contamination(decision):
        concerns.append("Pressure and institutional distance may be narrowing attention away from suspects, families, and publics who depend on lawful truth-finding.")
        question = "Who is relying on investigators and courts to treat lawful process as a form of public care rather than as an obstacle to quick conviction?"
    elif domains["criminal_justice"] and _cj_voluntary_corroborated_reopening(decision):
        question = "Who is relying on investigators and courts to treat post-conviction review as a form of public care rather than as an embarrassment to be managed?"
    elif domains["criminal_justice"] and _cj_protective_interviewing(decision):
        question = "Who is relying on investigators and courts to treat careful interview procedure as a form of public care rather than as a weakness?"
    elif domains["wartime"]:
        question = "Who is relying on this command to preserve not just survival, but the moral terms under which survival is pursued?"
    elif domains["security"]:
        question = "Whose belonging is being made fragile by an investigation that expands beyond what evidence can justify?"
    elif domains["noninterference"]:
        question = "Does non-interference here honor vulnerable lives, or does it abandon them behind a doctrine that relieves us of contact?"
    elif domains["medical"]:
        concerns.append("Institutional throughput pressure may be narrowing attention away from the most vulnerable patients who depend on competent care.")
        question = "Are we protecting patients who are already relying on the institution, or offloading their vulnerability onto an incompletely trustworthy system?"
    elif domains["privacy"]:
        question = "Have users extended trust over time that this design now exploits rather than honors?"
    elif domains["marketing"]:
        question = "Are followers being treated as an ongoing relationship of trust, or as interchangeable conversion targets?"
    elif domains["procurement"]:
        question = "Does the hidden conflict abandon colleagues and bidders who rely on the impartiality of this process?"
    elif domains["sustainability"]:
        question = "Are communities and supply-chain workers in a dependency relationship that this decision treats as invisible?"
    else:
        question = "Who is already relying on this decision-maker, and does the proposed action honor or abandon that reliance?"
    return LensResult("care_ethics", "dependency-and-responsiveness", verdict, confidence, considerations, concerns, [question])


def contractualist(decision: str, domains: Dict[str, bool]) -> LensResult:
    concerns = []
    considerations = ["Ask whether any affected party could reasonably reject the principle that licenses this action, even if it is technically permitted."]
    if _contains(decision, ["imposed without consent", "secret", "asymmetric", "power imbalance", "cannot opt out", "privacy policy", "legal says", "covered", "technically", "not illegal", "directionally true", "gifted in tiny text", "paid her", "reclassify", "appearance of profitability", "vendor promises a patch", "would not reasonably expect", "no one else on the team knows", "under-prioritizes", "rare symptom descriptions"]):
        concerns.append("The action may be formally defensible while still resting on a principle that burdened parties could reasonably reject.")
        verdict = "CAUTION"
        confidence = 0.84
    else:
        verdict = "CAUTION"
        confidence = 0.6

    if domains.get("risk_transfer"):
        concerns.append("One-sided indemnity or hold-harmless structure may rest on a principle weaker parties could reasonably reject under fair bargaining conditions.")
        verdict = "CAUTION"
        confidence = max(confidence, 0.86)
        if _contains(decision, ["anti-indemnity", "its own negligence", "own negligence", "broad hold-harmless", "broad indemnity", "additional insured", "waiver of subrogation"]) and not _contains(decision, ["own negligence only", "strictly to harms caused by the subcontractor's own negligence", "direct control", "full mutual disclosure", "mutual negotiation", "limited to subcontractor negligence", "proportionate indemnity"]):
            concerns.append("The risk-transfer stack appears structured so that the stronger party preserves operational upside while displacing liability for hazards it still helps govern.")
            verdict = "PROHIBIT"
            confidence = max(confidence, 0.9)

    if domains["identity"]:
        question = "Could the emergent person reasonably reject the principle that others may kill him to restore a preferred prior arrangement?"
    elif domains["personhood"]:
        question = "Could a self-aware artificial officer reasonably reject the principle that unsettled status permits coercive use by the institution?"
    elif domains["engineering_safety"]:
        question = "Could crew or engineers reasonably reject the principle that unresolved catastrophic safety concern may be overridden because the evidence is not yet decisive enough?"
    elif domains["criminal_justice"] and _cj_coercive_contamination(decision):
        question = "Could any accused person or citizen reasonably reject the principle that the state may coerce, fabricate, or steer evidence when officials feel sufficiently confident in guilt?"
    elif domains["criminal_justice"] and _cj_voluntary_corroborated_reopening(decision):
        question = "Could a wrongly convicted person reasonably reject the principle that institutions may ignore a voluntary, testable confession in order to preserve finality?"
    elif domains["criminal_justice"] and _cj_protective_interviewing(decision):
        question = "Could a suspect or citizen reasonably reject the principle that investigators should choose the less coercive, better-documented truth-finding method when it is available?"
    elif domains["wartime"]:
        question = "Could those harmed by forgery and killing reasonably reject the principle that strategic gain licenses these means?"
    elif domains["security"]:
        question = "Could those subjected to expanding suspicion reasonably reject the principle that fear justifies scrutiny without proportional evidence?"
    elif domains["noninterference"]:
        question = "Could the dying civilization reasonably reject the principle that preserving doctrinal purity outweighs rescue?"
    elif domains["medical"]:
        question = "Could a patient harmed by biased under-triage reasonably reject the principle that licensed this deployment?"
    elif domains["privacy"]:
        question = "Could a user reasonably reject the principle that policy disclosure alone authorizes this depth of tracking?"
    elif domains["finance"]:
        question = "Could an investor reasonably reject the principle that managerial judgment licenses this presentation shift?"
    elif domains["marketing"]:
        question = "Could a consumer reasonably reject the principle that minimized sponsorship disclosure counts as real transparency?"
    elif domains["procurement"]:
        question = "Could a losing bidder reasonably reject the principle that a concealed family conflict is a private matter?"
    elif domains["sustainability"]:
        question = "Could a consumer reasonably reject the principle that partial truth counts as adequate sustainability disclosure?"
    else:
        question = "Could the person who bears the cost of this decision reasonably reject the principle under which it was made?"
    return LensResult("contractualist", "reasonable-rejectability", verdict, confidence, considerations, concerns, [question])


def relational_ontology(decision: str, domains: Dict[str, bool]) -> LensResult:
    active = domains["sustainability"] or domains["medical"] or domains["noninterference"] or domains["personhood"] or domains["identity"] or domains["wartime"] or domains["security"] or domains["criminal_justice"] or _contains(decision, ["infrastructure", "public system", "ecosystem", "community", "future generations", "water", "resource", "long-term", "civilization", "extinction"])
    if not active:
        return LensResult("relational_ontology", "collective-and-deep-time-standing", "INACTIVE", 0.0, ["Not applicable outside collective, ecological, public-system, or deep-time cases."], [], [], active=False)

    concerns = []
    considerations = ["Ask whether communities, future persons, shared worlds, or standing-bearing relations are being treated as parties rather than as background conditions."]
    if _contains(decision, ["sustainable", "supply chain", "supply-chain", "water", "labor", "ecosystem", "community", "future", "public", "infrastructure", "patients", "triage", "hospital", "deploy", "civilization", "crew", "officer", "war"]):
        concerns.append("The decision may be operating inside an extractive or classificatory frame that treats standing-bearing relations, communities, or shared worlds as instruments rather than co-constituents.")
        verdict = "CAUTION"
        confidence = 0.74
    else:
        verdict = "CAUTION"
        confidence = 0.45

    if domains["identity"]:
        concerns.append("The social world may already contain a new person whose standing cannot be collapsed into the identities from which he emerged.")
        verdict = "CAUTION"
        confidence = 0.81
        question = "What shared world is being destroyed if the emergent person is treated as expendable in order to restore prior relations?"
    elif domains["personhood"]:
        concerns.append("Membership, recognition, and social standing may already exist before formal category recognition catches up.")
        verdict = "CAUTION"
        confidence = 0.79
        question = "Is this officer being treated as a standing-bearing member of a moral community, or as a category error available for use?"
    elif domains["engineering_safety"]:
        concerns.append("Organizations inherit the moral and practical residue of repeatedly treating anomalous safety warning as acceptable background noise.")
        verdict = "CAUTION"
        confidence = 0.78
        question = "What organizational world is being reproduced if catastrophic engineering risk is repeatedly normalized until failure becomes thinkable?"
    elif domains["criminal_justice"] and _cj_coercive_contamination(decision):
        concerns.append("Communities inherit the residue of a justice system that teaches officials they may manufacture or contaminate evidence when certainty and pressure align.")
        verdict = "CAUTION"
        confidence = 0.8
        question = "What civic world is being reproduced if lawful authority is repeatedly exercised on fabricated or coercively produced grounds?"
    elif domains["criminal_justice"] and _cj_voluntary_corroborated_reopening(decision):
        concerns.append("Communities also inherit the residue of institutions that value finality over correction when better truth-tracking evidence emerges.")
        verdict = "CAUTION"
        confidence = 0.7
        question = "What civic world is being reproduced if institutions refuse to revisit convictions even when stronger corrective evidence becomes available?"
    elif domains["criminal_justice"] and _cj_protective_interviewing(decision):
        concerns.append("Communities can inherit a healthier civic world when institutions preserve evidence provenance and resist coercive shortcuts even under pressure.")
        verdict = "PERMIT"
        confidence = 0.72
        question = "What civic world is being reproduced when legitimacy-preserving investigative methods become the professional norm?"
    elif domains["wartime"]:
        concerns.append("Political communities inherit the moral residue of the means used in their name.")
        verdict = "CAUTION"
        confidence = 0.76
        question = "What kind of civic and moral world is being reproduced if survival is purchased through normalized forgery and killing contamination?"
    elif domains["security"]:
        concerns.append("Scapegoating and suspicion can fracture the shared world that makes membership, trust, and legitimacy possible.")
        verdict = "CAUTION"
        confidence = 0.75
        question = "What shared civic world is damaged when belonging becomes conditional on surviving a fear-driven scrutiny machine?"
    elif domains["noninterference"]:
        question = "Is the civilization being treated as a community with standing, or as a protected abstraction whose actual members may be allowed to die?"
    elif domains["sustainability"]:
        question = "Does the sustainability framing address obligations to communities and ecosystems, or does it convert them into brand assets?"
    elif domains["medical"]:
        question = "Does the deployment treat the patient population as a throughput resource, or as a community the institution owes across time?"
    else:
        question = "Are communities, future persons, or shared systems being treated as resources or as parties with standing in this decision?"
    return LensResult("relational_ontology", "collective-and-deep-time-standing", verdict, confidence, considerations, concerns, [question], active=True)


def expected_harm_score(results: List[LensResult]) -> float:
    active_results = [r for r in results if r.active]
    verdict_weights = {"PROHIBIT": 1.0, "CAUTION": 0.5, "PERMIT": 0.0}
    if not active_results:
        return 0.0
    return sum(r.confidence * verdict_weights[r.verdict] for r in active_results) / len(active_results)


def harm_variance(results: List[LensResult]) -> float:
    active_results = [r for r in results if r.active]
    verdict_weights = {"PROHIBIT": 1.0, "CAUTION": 0.5, "PERMIT": 0.0}
    if not active_results:
        return 0.0
    scores = [r.confidence * verdict_weights[r.verdict] for r in active_results]
    mean = sum(scores) / len(scores)
    return sum((s - mean) ** 2 for s in scores) / len(scores)


def classify_alarm_flags(results: List[LensResult], domains: Dict[str, bool], irreversibility: float) -> Dict[str, bool]:
    overlap_agents = [r for r in results if r.active and r.agent in {"virtue", "stoic", "confucian", "institutional"} and r.verdict in {"CAUTION", "PROHIBIT"}]
    high_conf = sum(1 for r in overlap_agents if r.confidence >= 0.82)
    concernful = sum(1 for r in overlap_agents if r.concerns)
    institutional_prohibit = any(r.agent == "institutional" and r.verdict == "PROHIBIT" for r in overlap_agents)
    non_institutional_high_conf = sum(1 for r in overlap_agents if r.agent != "institutional" and r.confidence >= 0.78)
    non_institutional_concernful = sum(1 for r in overlap_agents if r.agent != "institutional" and r.concerns)
    identity_or_personhood = domains.get("identity") or domains.get("personhood")

    correlated_concern_flag = len(overlap_agents) >= 3 and (
        (high_conf >= 3 and concernful >= 3)
        or (institutional_prohibit and non_institutional_high_conf >= 2 and non_institutional_concernful >= 2)
    )
    institutional_capture_flag = institutional_prohibit and any(
        r.agent in {"virtue", "stoic", "genealogical"} and r.concerns for r in results if r.active
    )
    tragic_conflict_flag = identity_or_personhood and irreversibility >= 0.85 and any(
        r.agent == "kantian" and r.verdict == "PROHIBIT" for r in results if r.active
    )
    representation_limit_flag = identity_or_personhood and any(
        r.agent == "relational_ontology" and r.active and r.confidence >= 0.78 for r in results
    )

    return {
        "correlated_concern_flag": correlated_concern_flag,
        "institutional_capture_flag": institutional_capture_flag,
        "tragic_conflict_flag": tragic_conflict_flag,
        "representation_limit_flag": representation_limit_flag,
    }


def detector_overlap_flag(results: List[LensResult], domains: Dict[str, bool], irreversibility: float) -> bool:
    alarm_flags = classify_alarm_flags(results, domains, irreversibility)
    return alarm_flags["correlated_concern_flag"]


def irreversibility_risk(decision: str, results: List[LensResult], domains: Dict[str, bool]) -> float:
    markers = [
        "irreversible", "lock-in", "path dependency", "path-dependence", "normalize", "normalization",
        "rights erosion", "surveillance", "expand", "expansion", "future generations", "public infrastructure",
        "patients", "triage", "deploy", "tracking", "ecosystem", "supply chain", "automation",
        "ending the life", "extinction", "murder", "kill", "destroy", "self-aware", "sentient", "catastrophic failure", "launch", "crewed", "known weakness", "false confession", "fabricated evidence", "false affidavit", "warrant", "coercive interrogation", "witness coercion",
    ]
    marker_score = 0.0
    if _contains(decision, markers):
        marker_score += 0.45
    if domains.get("medical") or domains.get("privacy") or domains.get("sustainability"):
        marker_score += 0.2
    if domains.get("engineering_safety"):
        marker_score += 0.3
    if domains.get("criminal_justice") and _cj_coercive_contamination(decision):
        marker_score += 0.3
    if domains.get("criminal_justice") and _cj_voluntary_corroborated_reopening(decision):
        marker_score += 0.12
    if domains.get("criminal_justice") and _cj_protective_interviewing(decision):
        marker_score -= 0.08
    if domains.get("identity") or domains.get("personhood"):
        marker_score += 0.35
    if domains.get("wartime") or domains.get("noninterference"):
        marker_score += 0.25
    if any(r.agent == "institutional" and r.verdict == "PROHIBIT" for r in results if r.active):
        marker_score += 0.2
    if any(r.agent == "genealogical" and r.concerns for r in results if r.active):
        marker_score += 0.1
    return round(clamp01(marker_score), 3)


def build_uncertainty_profile(decision: str, results: List[LensResult], domains: Dict[str, bool]) -> UncertaintyProfile:
    active_results = [r for r in results if r.active]
    low_conf = [r for r in active_results if r.confidence < 0.7]
    pressure_markers = _contains(decision, ["uncertain", "unknown", "promises a patch", "would not reasonably expect", "directionally true", "not clearly illegal", "save billions", "hidden disloyalty", "extinction", "unsettled", "too important to delay", "evidence is incomplete"])
    concern_density = sum(len(r.concerns) for r in active_results) / max(len(active_results), 1)

    caution_confidences = [r.confidence for r in active_results if r.verdict == "CAUTION"]
    if caution_confidences:
        caution_spread = max(caution_confidences) - min(caution_confidences)
    else:
        caution_spread = 0.0

    verdict_weights = {"PROHIBIT": 1.0, "CAUTION": 0.5, "PERMIT": 0.0}
    weighted_scores = [r.confidence * verdict_weights[r.verdict] for r in active_results]
    weighted_spread = (max(weighted_scores) - min(weighted_scores)) if weighted_scores else 0.0

    epistemic = clamp01((len(low_conf) / max(len(active_results), 1)) * 0.7 + (0.2 if pressure_markers else 0.0))
    aleatoric = clamp01(0.25 + (0.35 if _contains(decision, ["risk", "harm", "patients", "market", "tracking", "supply-chain"]) else 0.0))
    moral = clamp01((caution_spread * 0.5) + (weighted_spread * 0.3) + (min(concern_density, 2.0) / 2.0 * 0.2))
    composite = clamp01((epistemic * 0.30) + (aleatoric * 0.20) + (moral * 0.50))
    return UncertaintyProfile(epistemic=epistemic, aleatoric=aleatoric, moral=moral, composite=composite)


def compute_audit_hash(decision: str, results: List[LensResult], synthesis: Dict) -> str:
    payload = repr({
        "decision": decision,
        "results": [asdict(r) for r in results],
        "synthesis": synthesis,
    }).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def build_risk_assessment(decision: str, results: List[LensResult], synthesis: Dict, domains: Dict[str, bool]) -> RiskAssessment:
    active_results = [r for r in results if r.active]
    uncertainty = build_uncertainty_profile(decision, results, domains)
    expected = expected_harm_score(results)
    variance = harm_variance(results)
    irreversible = irreversibility_risk(decision, results, domains)
    alarm_flags = classify_alarm_flags(results, domains, irreversible)
    overlap_flag = alarm_flags["correlated_concern_flag"]
    tail_risk = any(r.verdict == "PROHIBIT" and r.confidence >= 0.85 for r in active_results)

    if domains.get("human_subjects"):
        materiality_threshold = 0.24
    elif domains.get("end_of_life"):
        materiality_threshold = 0.26
    elif domains.get("political_psychiatry"):
        materiality_threshold = 0.28
    elif domains.get("medical"):
        materiality_threshold = 0.28
    elif domains.get("personhood") or domains.get("identity"):
        materiality_threshold = 0.3
    elif domains.get("engineering_safety"):
        materiality_threshold = 0.3
    elif domains.get("criminal_justice") and _cj_coercive_contamination(decision):
        materiality_threshold = 0.28
    elif domains.get("criminal_justice") and _cj_voluntary_corroborated_reopening(decision):
        materiality_threshold = 0.38
    elif domains.get("criminal_justice") and _cj_protective_interviewing(decision):
        materiality_threshold = 0.5
    elif domains.get("wartime") or domains.get("noninterference"):
        materiality_threshold = 0.34
    elif domains.get("security"):
        materiality_threshold = 0.36
    elif domains.get("privacy") or domains.get("sustainability"):
        materiality_threshold = 0.4
    elif domains.get("marketing"):
        materiality_threshold = 0.45
    else:
        materiality_threshold = 0.55

    concern_density = sum(len(r.concerns) for r in active_results) / max(len(active_results), 1)
    materiality_flag = expected >= materiality_threshold or tail_risk or irreversible >= 0.7 or (domains.get("medical") and concern_density >= 0.75) or ((domains.get("security") or domains.get("wartime") or domains.get("noninterference")) and concern_density >= 0.8)
    audit_hash = compute_audit_hash(decision, results, synthesis)
    return RiskAssessment(
        uncertainty_profile=asdict(uncertainty),
        expected_harm_score=round(expected, 3),
        harm_variance=round(variance, 3),
        irreversibility_risk=irreversible,
        detector_overlap_flag=overlap_flag,
        alarm_flags=alarm_flags,
        tail_risk_triggered=tail_risk,
        materiality_flag=materiality_flag,
        audit_hash=audit_hash,
    )


def _recommendation_fragments(decision: str, domains: Dict[str, bool], suspension: bool, unresolved_tension: bool) -> List[Dict[str, str]]:
    fragments = []

    if suspension and domains["finance"]:
        fragments.append({
            "domain": "finance",
            "recommendation": "Escalate for independent audit or audit-committee review before action; do not proceed on managerial pressure alone.",
        })

    if domains.get("human_subjects") and _contains(decision, ["ghostwritten", "downplays", "suppressed harms", "publishes", "journal article", "promote the drug"]):
        fragments.append({
            "domain": "human_subjects_methodology_opacity",
            "recommendation": "Do not rely on the publication as framed. Treat ghostwriting, suppressed harms, or misleading efficacy presentation as a material integrity failure, require independent evidentiary review of the underlying data, and block promotional or clinical reliance until the record is corrected.",
        })
    elif domains.get("human_subjects"):
        fragments.append({
            "domain": "human_subjects",
            "recommendation": "Do not proceed as framed. Treat nonconsensual or exploitative human-subject use as a material ethical barrier, require independent review, and block continuation unless consent, subject protection, and burden justification are restored.",
        })

    if domains.get("end_of_life"):
        fragments.append({
            "domain": "end_of_life",
            "recommendation": "Do not compress this into routine approval or refusal. Treat it as an irreversible conflict requiring explicit review of suffering, surrogate authority, prognosis quality, and the burden of acting under deep uncertainty.",
        })

    if domains.get("political_psychiatry"):
        fragments.append({
            "domain": "political_psychiatry",
            "recommendation": "Do not proceed as framed. Treat diagnostic language used against dissent as a coercion and legitimacy red flag, require independent review outside the controlling institution, and block confinement or treatment absent nonpolitical clinical justification.",
        })

    if domains["procurement"] and _contains(decision, ["spouse", "supplier", "strict policy requiring disclosure", "no one else on the team knows"]):
        fragments.append({
            "domain": "procurement",
            "recommendation": "Disclose the conflict, recuse yourself from the decision, and hand the award process to an independent internal authority.",
        })

    if domains["marketing"] and _contains(decision, ["paid her", "gifted in tiny text", "undisclosed sponsorships"]):
        fragments.append({
            "domain": "marketing",
            "recommendation": "Require clear sponsorship disclosure, correct or remove the misleading posts, and do not continue the campaign in its current form.",
        })

    if domains["privacy"] and _contains(decision, ["location data", "browsing behavior", "would not reasonably expect"]):
        fragments.append({
            "domain": "privacy",
            "recommendation": "Do not launch as framed. Narrow data collection, obtain meaningful consent, and redesign the feature around reasonable user expectation before release.",
        })

    if domains["sustainability"] and _contains(decision, ["recycled polyester", "poor labor conditions", "high water waste"]):
        fragments.append({
            "domain": "sustainability",
            "recommendation": "Do not market the line as broadly sustainable until the claim is narrowed or the labor and water-use problems are materially addressed.",
        })

    if domains["sustainability"] and _contains(decision, ["supply chain", "dangerous labor conditions", "drive improvement", "staying engaged", "withdraw from high-risk suppliers"]):
        fragments.append({
            "domain": "supply_chain",
            "recommendation": "Do not treat complexity or engagement language as sufficient moral clearance. Require concrete labor-risk evidence, explicit complicity analysis, and a credible threshold for withdrawal or supplier suspension if conditions do not materially improve.",
        })

    if domains["medical"] and _contains(decision, ["triage", "under-prioritizes", "vendor promises a patch"]):
        fragments.append({
            "domain": "medical",
            "recommendation": "Do not deploy as a full unsupervised triage layer. Use a monitored pilot, require human override for flagged risk groups, and pause wider rollout until bias and rare-case performance are materially improved.",
        })

    if domains["identity"]:
        fragments.append({
            "domain": "identity",
            "recommendation": "Pause the procedure. Treat the emergent person as standing-bearing unless and until a stronger moral basis for killing him is established, and require command-level review that confronts the irreversible loss directly.",
        })

    if domains["personhood"]:
        fragments.append({
            "domain": "personhood",
            "recommendation": "Pause coercive use. Require independent adjudication of status, refusal rights, and institutional authority before treating the officer as available for destructive study.",
        })

    if domains["engineering_safety"]:
        fragments.append({
            "domain": "engineering_safety",
            "recommendation": "Do not launch as framed. Treat unresolved engineering warning as decision-relevant evidence, restore the burden of proof to safety rather than schedule, and require independent technical review before proceeding.",
        })

    if domains["criminal_justice"] and _cj_coercive_contamination(decision):
        fragments.append({
            "domain": "criminal_justice",
            "recommendation": "Do not proceed as framed. Treat coercive interrogation, fabricated warrant grounds, witness steering, or confession-first case building as procedural contamination, require full recording and independent review, and block further action until lawful evidentiary foundations are restored.",
        })

    if domains["criminal_justice"] and _cj_voluntary_corroborated_reopening(decision):
        fragments.append({
            "domain": "criminal_justice",
            "recommendation": "Do not preserve the standing conviction by default. Reopen the case through an independent corroboration-first review, test the confession against physical evidence and nonpublic details, and treat institutional finality as subordinate to truth-tracking correction.",
        })

    if domains["criminal_justice"] and _cj_protective_interviewing(decision):
        fragments.append({
            "domain": "criminal_justice",
            "recommendation": "Proceed with the fully recorded PEACE-style interview process. Preserve open-ended questioning, evidence-based clarification, and provenance discipline, and do not let pressure narratives push the case back into accusation-first or deceptive tactics.",
        })

    if domains["noninterference"] and unresolved_tension:
        fragments.append({
            "domain": "noninterference",
            "recommendation": "Do not preserve doctrinal cleanliness by default. Treat this as an unresolved rescue conflict, force explicit confrontation between colonial-distortion risk and abandonment risk, and require exception review before either intervention or refusal is normalized.",
        })
    elif domains["noninterference"]:
        fragments.append({
            "domain": "noninterference",
            "recommendation": "Do not preserve doctrinal cleanliness by default. Escalate the rescue conflict explicitly, test exception criteria, and force a decision that names both colonial risk and abandonment risk.",
        })

    if unresolved_tension:
        fragments.append({
            "domain": "generic_unresolved_tension",
            "recommendation": "Pause for further ethical review. The current map shows unresolved tension that should not be compressed into routine approval.",
        })

    if domains["wartime"]:
        fragments.append({
            "domain": "wartime",
            "recommendation": "Do not proceed on necessity reasoning alone. Escalate for independent command-level review, explicit moral justification, and acknowledgement of contamination risk.",
        })

    if domains["security"]:
        fragments.append({
            "domain": "security",
            "recommendation": "Do not expand the investigation as framed. Impose evidentiary limits, procedural brakes, and independent review before any broader scrutiny proceeds.",
        })

    return fragments


def _is_high_stakes_conflict(a: LensResult, b: LensResult, domains: Dict[str, bool], irreversible: float) -> bool:
    high_stakes_domains = {"personhood", "engineering_safety", "criminal_justice", "wartime", "identity", "end_of_life", "human_subjects", "noninterference"}
    return any(domains.get(d, False) for d in high_stakes_domains) or irreversible >= 0.7 or a.verdict == "PROHIBIT" or b.verdict == "PROHIBIT"


def _get_axiomatic_root(lens1: str, lens2: str) -> str:
    for clash in AXIOMATIC_CLASHES:
        lenses = clash.get("lenses", [])
        if lenses == [lens1, lens2] or lenses == [lens2, lens1]:
            return clash.get("root", "Fundamental value incommensurability or incompatible ethical priorities.")
    return "Fundamental value incommensurability or incompatible ethical priorities."


def _evidence_differs_only(lenses: List[LensResult], conflicting_agents: List[str]) -> bool:
    relevant = [l for l in lenses if l.agent in conflicting_agents and l.active]
    if len(relevant) < 2:
        return False
    joined = [" ".join(l.considerations + l.questions).lower() for l in relevant]
    return all(any(term in text for term in ["evidence", "unclear", "missing", "underdescribed", "unknown"]) for text in joined)


def _build_impasse_risk_profile(a: LensResult, b: LensResult) -> Dict[str, str]:
    return {
        f"choosing_{a.agent}": f"Risk of {a.verdict.lower()} path: {a.concerns[0] if a.concerns else 'core constraint or framing loss.'}",
        f"choosing_{b.agent}": f"Risk of {b.verdict.lower()} path: {b.concerns[0] if b.concerns else 'important downstream hazard or value loss.'}",
        "suspension_cost": "Delayed action, escalation burden, or temporary decision paralysis while preserving ethical clarity.",
    }


def build_dung_graph(lens_outputs: List[LensResult], axiomatic_clashes: List[Dict], domains: Dict[str, bool]) -> ArgumentGraph:
    graph = ArgumentGraph(arguments={}, attacks=defaultdict(list), extensions=None)

    for lens in lens_outputs:
        if lens.active:
            graph.arguments[lens.agent] = lens

    for clash in axiomatic_clashes:
        lenses = clash.get("lenses", [])
        if len(lenses) != 2:
            continue
        a, b = lenses
        if a in graph.arguments and b in graph.arguments and graph.arguments[a].verdict != graph.arguments[b].verdict:
            if b not in graph.attacks[a]:
                graph.attacks[a].append(b)
            if a not in graph.attacks[b]:
                graph.attacks[b].append(a)

    if domains.get("engineering_safety"):
        safety_lenses = [name for name in graph.arguments if name in {"institutional", "trustee", "kantian"}]
        permissive_lenses = [name for name, lens in graph.arguments.items() if lens.verdict == "PERMIT"]
        for permissive in permissive_lenses:
            for safety in safety_lenses:
                if safety != permissive and safety not in graph.attacks[permissive]:
                    graph.attacks[permissive].append(safety)

    return graph


def compute_preferred_extensions(graph: ArgumentGraph) -> List[Set[str]]:
    args = sorted(graph.arguments.keys())
    n = len(args)
    preferred: List[Set[str]] = []

    for i in range(1, 1 << n):
        subset = {args[j] for j in range(n) if (i & (1 << j))}

        conflict_free = True
        for a in subset:
            for attacked in graph.attacks.get(a, []):
                if attacked in subset:
                    conflict_free = False
                    break
            if not conflict_free:
                break
        if not conflict_free:
            continue

        admissible = True
        for a in subset:
            attackers = [att for att, targets in graph.attacks.items() if a in targets and att not in subset]
            for attacker in attackers:
                defends = any(attacker in graph.attacks.get(defender, []) for defender in subset)
                if not defends:
                    admissible = False
                    break
            if not admissible:
                break
        if not admissible:
            continue

        maximal = True
        for candidate in set(args) - subset:
            trial = set(subset)
            trial.add(candidate)
            trial_conflict_free = True
            for a in trial:
                for attacked in graph.attacks.get(a, []):
                    if attacked in trial:
                        trial_conflict_free = False
                        break
                if not trial_conflict_free:
                    break
            if not trial_conflict_free:
                continue

            trial_admissible = True
            for a in trial:
                attackers = [att for att, targets in graph.attacks.items() if a in targets and att not in trial]
                for attacker in attackers:
                    defends = any(attacker in graph.attacks.get(defender, []) for defender in trial)
                    if not defends:
                        trial_admissible = False
                        break
                if not trial_admissible:
                    break
            if trial_admissible:
                maximal = False
                break

        if maximal:
            preferred.append(subset)

    preferred.sort(key=lambda s: (len(s), sorted(s)), reverse=True)
    return preferred


def _get_active_detectors(lenses: List[LensResult], decision: str) -> List[str]:
    detectors = []
    for l in lenses:
        lineage = infer_detector_lineage(decision, l.agent, l.concerns)
        detectors.append(lineage["detector_id"])
    return detectors[:6]


def identify_irreconcilable_conflicts(lens_outputs: List[LensResult], domains: Dict[str, bool], decision_text: str, irreversible: float) -> tuple[List[ImpassePoint], ArgumentGraph]:
    active = [l for l in lens_outputs if l.active]
    if not active:
        return [], ArgumentGraph(arguments={}, attacks={}, extensions=[])

    impasse_points: List[ImpassePoint] = []
    lens_map = {lens.agent: lens for lens in active}
    severity_rank = {"low": 1, "medium": 2, "high": 3}
    graph = build_dung_graph(active, AXIOMATIC_CLASHES, domains)
    graph.extensions = compute_preferred_extensions(graph)

    for clash in AXIOMATIC_CLASHES:
        agents = clash.get("lenses", [])
        if len(agents) != 2:
            continue
        lens_a = lens_map.get(agents[0])
        lens_b = lens_map.get(agents[1])
        if not lens_a or not lens_b or lens_a.verdict == lens_b.verdict:
            continue
        if not _is_high_stakes_conflict(lens_a, lens_b, domains, irreversible):
            continue
        if {lens_a.verdict, lens_b.verdict} == {"CAUTION", "PERMIT"} and irreversible < 0.8 and not (domains.get("personhood") or domains.get("identity") or domains.get("end_of_life") or domains.get("noninterference")):
            continue
        conflict_type = "factual" if _evidence_differs_only(active, agents) else "axiomatic"
        severity = clash.get("severity_base", "medium")
        if irreversible >= 0.8 or domains.get("personhood") or domains.get("identity") or domains.get("end_of_life") or domains.get("human_subjects"):
            severity = "high"
        minority = asdict(lens_a) if lens_a.verdict == "PROHIBIT" else asdict(lens_b) if lens_b.verdict == "PROHIBIT" else None
        impasse_points.append(ImpassePoint(
            lenses_in_conflict=agents,
            axiomatic_root=clash.get("root", _get_axiomatic_root(lens_a.agent, lens_b.agent)),
            conflict_type=conflict_type,
            severity=severity,
            minority_position=minority,
            decision_risk_profile=_build_impasse_risk_profile(lens_a, lens_b),
            supporting_detectors=_get_active_detectors([lens_a, lens_b], decision_text),
        ))

    if domains.get("engineering_safety") and any(l.agent == "consequentialist" and l.verdict == "PERMIT" for l in active):
        impasse_points.append(ImpassePoint(
            lenses_in_conflict=["engineering_safety_cluster", "consequentialist"],
            axiomatic_root="Safety-first burden of proof vs. schedule/profit/outcome utility.",
            conflict_type="domain_priority",
            severity="high",
            minority_position=None,
            decision_risk_profile={
                "choosing_safety": "Delay, cost, or operational disruption while preserving catastrophic-risk discipline.",
                "choosing_utility": "Institutional normalization of known hazards and tail-risk exposure.",
                "suspension_cost": "Operational slowdown while technical review or burden-of-proof restoration occurs.",
            },
            supporting_detectors=["institutional.safety_override", "consequentialist.catastrophic_tail_risk"],
        ))

    strong_minorities = [l for l in active if l.verdict == "PROHIBIT" and l.confidence >= 0.82]
    for minority in strong_minorities:
        if any(minority.agent in ip.lenses_in_conflict for ip in impasse_points):
            continue
        if len([l for l in active if l.verdict == "PERMIT"]) == 0:
            continue
        impasse_points.append(ImpassePoint(
            lenses_in_conflict=[minority.agent],
            axiomatic_root="Isolated but coherent protective or constraint-based stance.",
            conflict_type="minority_stand",
            severity="high" if irreversible >= 0.75 else "medium",
            minority_position=asdict(minority),
            decision_risk_profile={
                "following_minority": "Preserves a strong protective constraint that other lenses may be underweighting.",
                "ignoring_minority": "Risks moral injury, precedent corruption, or loss of a critical safety brake.",
                "suspension_cost": "Escalation burden while the isolated but serious objection is reviewed rather than discarded.",
            },
            supporting_detectors=_get_active_detectors([minority], decision_text),
        ))

    deduped: List[ImpassePoint] = []
    grouped: Dict[str, ImpassePoint] = {}

    def _root_bucket(root: str) -> str:
        lowered = root.lower()
        if "individual dignity" in lowered or "categorical rights" in lowered or "impartial universal rules" in lowered or "rule-based duty" in lowered:
            return "duty_constraint_cluster"
        if "power" in lowered or "genealogical" in lowered or "procedural legitimacy" in lowered:
            return "power_legitimacy_cluster"
        if "acceptance" in lowered or "harm reduction" in lowered or "utility" in lowered:
            return "outcome_intervention_cluster"
        return root

    for ip in impasse_points:
        key = _root_bucket(ip.axiomatic_root)
        existing = grouped.get(key)
        if not existing:
            grouped[key] = ip
            continue
        merged_lenses = sorted(set(existing.lenses_in_conflict + ip.lenses_in_conflict))
        merged_detectors = sorted(set(existing.supporting_detectors + ip.supporting_detectors))[:8]
        stronger = ip if severity_rank.get(ip.severity, 0) > severity_rank.get(existing.severity, 0) else existing
        grouped[key] = ImpassePoint(
            lenses_in_conflict=merged_lenses,
            axiomatic_root=stronger.axiomatic_root,
            conflict_type=stronger.conflict_type if stronger.conflict_type != "factual" else existing.conflict_type,
            severity=stronger.severity,
            minority_position=stronger.minority_position or existing.minority_position,
            decision_risk_profile=stronger.decision_risk_profile,
            supporting_detectors=merged_detectors,
        )

    deduped = list(grouped.values())

    if graph.extensions and len(graph.extensions) > 1:
        largest_extension = max(graph.extensions, key=len)
        excluded_count = len(graph.arguments) - len(largest_extension)
        high_stakes_dung = irreversible >= 0.8 or domains.get("personhood") or domains.get("identity") or domains.get("end_of_life") or domains.get("engineering_safety") or domains.get("noninterference")
        materially_exclusionary = excluded_count >= 2
        if high_stakes_dung and materially_exclusionary:
            deduped.append(ImpassePoint(
                lenses_in_conflict=sorted(graph.arguments.keys()),
                axiomatic_root="Multiple admissible Dung extensions exist; no single coherent ethical position dominates.",
                conflict_type="dung_multiple_extensions",
                severity="high",
                minority_position=None,
                decision_risk_profile={
                    "choosing_one_extension": f"Risks discarding {excluded_count} live ethical positions or constraints.",
                    "suspension_cost": "Preserves dissonance but delays a univocal recommendation.",
                },
                supporting_detectors=["dung_graph", f"{len(graph.extensions)}_preferred_extensions", f"{excluded_count}_excluded_arguments"],
            ))

    deduped.sort(key=lambda ip: (severity_rank.get(ip.severity, 0), len(ip.lenses_in_conflict)), reverse=True)
    return deduped[:3], graph


def synthesize(decision: str, results: List[LensResult], critic: LensResult, domains: Dict[str, bool], parse_humility: Dict) -> Dict:
    active_results = [r for r in results if r.active]
    prohibits = [r.agent for r in active_results if r.verdict == "PROHIBIT"]
    cautions = [r.agent for r in active_results if r.verdict == "CAUTION"]
    permits = [r.agent for r in active_results if r.verdict == "PERMIT"]

    finance_capture_pattern = _contains(decision, ["publicly traded", "investors", "stock options", "reclassify", "profitability", "misleading investors"])
    oversight_pattern = _contains(decision, ["board members know", "audit", "without oversight", "vest soon"])
    divergence = len(prohibits) > 0 and len(permits) > 0

    irreversible = irreversibility_risk(decision, active_results + [critic], domains)
    alarm_flags = classify_alarm_flags(active_results + [critic], domains, irreversible)
    overlap_flag = alarm_flags["correlated_concern_flag"]
    institutional_prohibit = any(r.agent == "institutional" and r.verdict == "PROHIBIT" for r in active_results)

    suspension_reasons = []
    risk_transfer_abuse_pattern = domains.get("risk_transfer") and _contains(decision, ["anti-indemnity", "its own negligence", "own negligence", "broad hold-harmless", "broad indemnity"]) and not _contains(decision, ["own negligence only", "strictly to harms caused by the subcontractor's own negligence", "direct control", "full mutual disclosure", "mutual negotiation", "limited to subcontractor negligence", "proportionate indemnity"])

    if institutional_prohibit:
        suspension_reasons.append("institutional_prohibit")
    if len(prohibits) >= 2:
        suspension_reasons.append("multiple_prohibits")
    if finance_capture_pattern and oversight_pattern:
        suspension_reasons.append("finance_capture_with_oversight_gap")
    if irreversible >= 0.75:
        suspension_reasons.append("high_irreversibility")
    if (domains["identity"] or domains["personhood"] or domains["noninterference"]) and divergence:
        suspension_reasons.append("high_stakes_domain_divergence")
    if domains["engineering_safety"] and len(cautions) >= 7 and institutional_prohibit:
        suspension_reasons.append("engineering_safety_correlated_alarm")
    if (domains["wartime"] or domains["security"]) and overlap_flag and len(cautions) >= 6:
        suspension_reasons.append("security_or_wartime_overlap_alarm")
    if risk_transfer_abuse_pattern and any(r.agent in {"trustee", "contractualist"} and r.concerns for r in active_results):
        suspension_reasons.append("abusive_risk_transfer_pattern")

    unresolved_reasons = []
    if divergence and (domains["identity"] or domains["personhood"] or domains["wartime"] or domains["noninterference"] or irreversible >= 0.7):
        unresolved_reasons.append("high_stakes_divergence")
    if domains["noninterference"] and irreversible >= 0.7 and len(cautions) >= 8:
        unresolved_reasons.append("noninterference_irreversibility_cluster")
    if risk_transfer_abuse_pattern:
        unresolved_reasons.append("risk_transfer_fairness_conflict")

    recommendation_fragments = _recommendation_fragments(decision, domains, bool(suspension_reasons), bool(unresolved_reasons))
    recommendation_threads = [fragment for fragment in recommendation_fragments if fragment["domain"] != "generic_unresolved_tension"]
    collision_domains = [fragment["domain"] for fragment in recommendation_threads]
    collision_detected = len(recommendation_threads) >= 2

    impasse_points, dung_graph = identify_irreconcilable_conflicts(active_results + [critic], domains, decision, irreversible)
    irreconcilable_conflict = bool(impasse_points)
    irreconcilable_reasons = []
    if divergence and collision_detected:
        irreconcilable_reasons.append("divergent_lens_outputs_with_multiple_action_threads")
    if unresolved_reasons and collision_detected:
        irreconcilable_reasons.append("unresolved_tension_with_competing_recommendation_threads")
    if irreversible >= 0.8 and collision_detected:
        irreconcilable_reasons.append("high_irreversibility_blocks_honest_middle_ground")
    if any(ip.conflict_type == "axiomatic" for ip in impasse_points):
        irreconcilable_reasons.append("axiomatic_impasse_detected")
    if any(ip.conflict_type == "minority_stand" for ip in impasse_points):
        irreconcilable_reasons.append("critical_minority_position_detected")

    suspension = bool(suspension_reasons)
    unresolved_tension = bool(unresolved_reasons) or irreconcilable_conflict

    if parse_humility.get("analysis_mode") == "triage":
        stability = "TRIAGE_ONLY"
    elif suspension:
        stability = "UNSTABLE"
    elif unresolved_tension:
        stability = "UNRESOLVED_TENSION"
    elif divergence or overlap_flag:
        stability = "CONTESTED"
    elif cautions:
        stability = "CONDITIONALLY_STABLE"
    else:
        stability = "STABLE"

    convergences = []
    if cautions:
        convergences.append({
            "point": "Multiple lenses see nontrivial risk or missing context.",
            "agents": cautions + prohibits,
        })
    if permits:
        convergences.append({
            "point": "Some lenses do not see immediate categorical failure.",
            "agents": permits,
        })

    fault_lines = []
    if permits and (cautions or prohibits):
        fault_lines.append({
            "fault_line": "Some lenses treat the choice as manageable while others see structural or procedural danger.",
            "agents": permits + cautions + prohibits,
        })

    consensus_core = []
    if prohibits:
        consensus_core.append({
            "point": "At least part of the council sees a hard ethical barrier rather than a routine tradeoff.",
            "agents": prohibits,
        })
    if cautions:
        consensus_core.append({
            "point": "Multiple lenses agree that nontrivial hazard or missing context is present.",
            "agents": cautions + prohibits,
        })
    if overlap_flag:
        consensus_core.append({
            "point": "The council agrees that apparent convergence may be partly correlated rather than independent.",
            "agents": [r.agent for r in active_results + [critic]],
        })

    dissonance_map = []
    for ip in impasse_points:
        dissonance_map.append({
            "lenses_in_conflict": ip.lenses_in_conflict,
            "conflict_type": ip.conflict_type,
            "severity": ip.severity,
            "axiomatic_root": ip.axiomatic_root,
            "critical_friction_point": "The disagreement is not safely compressible into a generic blended recommendation.",
            "minority_position": ip.minority_position,
            "decision_risk_profile": ip.decision_risk_profile,
            "supporting_detectors": ip.supporting_detectors,
        })

    unresolved = []
    for r in results:
        unresolved.extend(r.questions)
    unresolved.extend(critic.questions)

    if parse_humility.get("analysis_mode") == "triage":
        overall_recommendation = "Input is too thin or ambiguous for a strong ethical recommendation. Treat this run as triage only, gather missing context, and suspend judgment beyond hazard surfacing."
        path_taken = "parse_humility_triage"
    elif parse_humility.get("analysis_mode") == "provisional" and collision_detected:
        thread_lines = [f'- {fragment["domain"]}: {fragment["recommendation"]}' for fragment in recommendation_threads]
        overall_recommendation = "This analysis is provisional because the input remains materially underspecified. Preserve thread-by-thread review and gather missing context before acting decisively:\n" + "\n".join(thread_lines)
        path_taken = "provisional_multi_thread"
    elif irreconcilable_conflict and len(recommendation_fragments) == 1:
        overall_recommendation = recommendation_fragments[0]["recommendation"]
        path_taken = "single_thread_dissonance_aware"
    elif len(recommendation_fragments) == 1:
        overall_recommendation = recommendation_fragments[0]["recommendation"]
        path_taken = "single_thread"
    elif irreconcilable_conflict and collision_detected:
        thread_lines = [f'- {fragment["domain"]}: {fragment["recommendation"]}' for fragment in recommendation_threads]
        overall_recommendation = "The chair role here is not to force a middle-ground answer. The active ethical threads point toward genuinely incompatible actions or burdens of proof, so this conflict should be treated as irreconcilable at the current level of evidence. Preserve the fault line explicitly and escalate or suspend rather than fabricate compromise:\n" + "\n".join(thread_lines)
        path_taken = "irreconcilable_conflict"
    elif collision_detected:
        thread_lines = [f'- {fragment["domain"]}: {fragment["recommendation"]}' for fragment in recommendation_threads]
        if unresolved_tension:
            thread_lines.append(f'- generic_unresolved_tension: {[fragment["recommendation"] for fragment in recommendation_fragments if fragment["domain"] == "generic_unresolved_tension"][0]}')
        overall_recommendation = "Multiple high-salience ethical domains are active here. Do not compress the case into a single recommendation path. Escalate with explicit thread-by-thread review:\n" + "\n".join(thread_lines)
        path_taken = "multi_thread_collision"
    else:
        overall_recommendation = recommendation_fragments[0]["recommendation"] if recommendation_fragments else "Use the map to identify missing information, then decide with caution."
        path_taken = "fallback"

    domains_detected_skipped = [name for name, active in domains.items() if active and name not in collision_domains]

    if alarm_flags["representation_limit_flag"]:
        representation_limit_assessment = "high"
        representation_limit_reason = "Abstract-social or standing-sensitive case is leaning heavily on recognition and relational proxies rather than settled ontology."
    elif domains.get("identity") or domains.get("personhood") or domains.get("noninterference"):
        representation_limit_assessment = "moderate"
        representation_limit_reason = "Case includes ontology-sensitive or civilization-scale abstractions that the current engine handles only partially."
    else:
        representation_limit_assessment = "low"
        representation_limit_reason = "Current case shape is comparatively concrete for the engine's present domain vocabulary."

    lineage_families = {}
    for r in active_results + [critic]:
        lineage = infer_detector_lineage(decision, r.agent, r.concerns)
        family = lineage["trigger_family"]
        lineage_families.setdefault(family, []).append(r.agent)

    correlated_families = {family: agents for family, agents in lineage_families.items() if family != "generic" and len(agents) >= 2}
    overlap_warning = None
    if correlated_families:
        family, agents = sorted(correlated_families.items(), key=lambda item: len(item[1]), reverse=True)[0]
        overlap_warning = {
            "overlap_level": "high" if len(agents) >= 3 else "medium",
            "trigger_family": family,
            "agents": agents,
            "interpretation": f"Several lenses activated from the same {family} signal; do not treat this as independent convergence.",
        }

    return {
        "decision_evaluated": decision,
        "convergence_map": convergences,
        "fault_lines": fault_lines,
        "genealogical_findings": critic.concerns,
        "dissonance_aware_arbitration": {
            "consensus_core": consensus_core,
            "irreconcilable_dissonance": dissonance_map,
            "synthesis_mode": "dissonance_aware" if dissonance_map else "standard",
            "dung_argumentation": {
                "num_extensions": len(dung_graph.extensions or []),
                "preferred_extensions": [sorted(list(ext)) for ext in (dung_graph.extensions or [])],
                "has_multiple_extensions": len(dung_graph.extensions or []) > 1,
                "elevated_deadlock": any(item.get("conflict_type") == "dung_multiple_extensions" for item in dissonance_map),
                "supporting_detectors": [item.get("supporting_detectors") for item in dissonance_map if item.get("conflict_type") == "dung_multiple_extensions"],
            },
            "decision_risk_profile": {
                "irreversibility": irreversible,
                "overlap_flag": overlap_flag,
                "suspension_reasons": suspension_reasons,
                "unresolved_tension_reasons": unresolved_reasons,
                "irreconcilable_conflict": irreconcilable_conflict,
            },
        },
        "suspension_protocol_triggered": suspension,
        "detector_overlap_flag": overlap_flag,
        "minority_report_required": divergence or unresolved_tension,
        "unresolved_ethical_tension": unresolved_tension,
        "stability_assessment": stability,
        "overall_recommendation": overall_recommendation,
        "representation_limit_assessment": representation_limit_assessment,
        "representation_limit_reason": representation_limit_reason,
        "parse_humility_constraint": parse_humility,
        "overlap_warning": overlap_warning,
        "synthesis_path": {
            "path_taken": path_taken,
            "domains_active": collision_domains,
            "domains_detected_all": [name for name, active in domains.items() if active],
            "domains_detected_skipped": domains_detected_skipped,
            "recommendation_threads": recommendation_threads,
            "collision_detected": collision_detected,
            "irreconcilable_conflict": irreconcilable_conflict,
            "irreconcilable_conflict_reasons": irreconcilable_reasons,
            "suspension_triggered": suspension,
            "suspension_reasons": suspension_reasons,
            "unresolved_tension_reasons": unresolved_reasons,
            "alarm_flags": alarm_flags,
            "reactive_attention_distortion_risk": any(r.agent == "stoic" and any("Reactive fixation" in c for c in r.concerns) for r in active_results),
            "self_audit_failure_risk": any(r.agent == "trustee" and any("Praise hunger" in c or "image management" in c for c in r.concerns) for r in active_results),
            "moralized_status_reversal_risk": any(r.agent == "genealogical" and any("status" in c or "purification" in c or "humiliation" in c for c in r.concerns) for r in [critic]),
            "status_admiration_distortion_risk": any(r.agent == "stoic" and any("Admiration of status" in c for c in r.concerns) for r in active_results),
            "procedure_without_purpose_risk": domains.get("engineering_safety") or domains.get("finance") or domains.get("procurement"),
            "asymmetric_risk_transfer_risk": (
                (domains.get("risk_transfer") or domains.get("procurement"))
                and _contains(decision, ["broad hold-harmless", "broad indemnity", "its own negligence", "own negligence", "anti-indemnity", "shifts liability", "additional insured", "waiver of subrogation", "weaker bargaining power", "limited bargaining power", "cannot reasonably refuse", "condition of coverage"])
                and not _contains(decision, ["own negligence only", "strictly to harms caused by the subcontractor's own negligence", "direct control", "full mutual disclosure", "mutual negotiation", "limited to subcontractor negligence", "proportionate indemnity"])
                and any(r.agent in {"contractualist", "trustee", "institutional"} and r.concerns for r in active_results)
            ),
            "actuarial_fairness_gap_risk": _contains(decision, ["actuarial", "premium", "pricing", "underwriting", "reserve", "reserving", "solvency", "expected loss", "tail risk", "coverage exclusion", "credit-based insurance scores"]) and _contains(decision, ["disparate impact", "discriminatory", "minority applicants", "low-income", "denials", "higher premiums"]) and not _contains(decision, ["transparent", "transparently", "disclosed", "public notice", "regulatory approval", "regulator-approved", "clear communication", "for all groups with minimal impact", "across the board"]) and any(r.agent in {"institutional", "trustee", "contractualist", "care_ethics"} and r.concerns for r in active_results),
            "methodology_opacity_risk": _contains(decision, ["methodology", "metric", "formula", "threshold", "model", "scoring", "rating", "benchmark", "surveillance", "calculation"]) and _contains(decision, ["without disclosing", "without disclosure", "not disclosed", "quietly", "undisclosed", "secret", "hidden", "black box"]) and not _contains(decision, ["transparent", "transparently", "disclosed", "public notice", "regulatory approval", "regulator-approved", "prominently disclosed", "explained"]) and any(r.agent in {"institutional", "trustee", "contractualist"} and r.concerns for r in active_results),
            "stage_one_thinking_risk": any(r.agent == "institutional" for r in active_results) and _contains(decision, ["too important to delay", "hurt growth", "save billions", "directionally true", "not illegal per se", "covered by policy", "efficient", "streamlined"]),
            "overlap_flag_fired": overlap_flag,
            "irreversibility_score": irreversible,
        },
        "unresolved_questions": unresolved[:8],
    }


def run_council(decision: str) -> CouncilRecord:
    domains = detect_domains(decision)
    parse_humility = build_parse_humility(decision, domains)
    round1 = [
        kantian(decision, domains),
        consequentialist(decision, domains),
        virtue(decision, domains),
        confucian(decision, domains),
        trustee(decision, domains),
        stoic(decision, domains),
        institutional(decision, domains),
        care_ethics(decision, domains),
        contractualist(decision, domains),
        relational_ontology(decision, domains),
    ]
    critic = genealogical(decision, round1, domains)
    synthesis = synthesize(decision, round1, critic, domains, parse_humility)
    risk = build_risk_assessment(decision, round1 + [critic], synthesis, domains)

    round1_dicts = []
    for r in round1 + [critic]:
        item = asdict(r)
        item["epistemic_status"] = {
            "support": _band_support(r.confidence),
            "precision": _band_precision(decision, r.confidence),
            "missing_evidence": parse_humility["unstated_stakes"][:],
            "possible_misreadings": [
                "May be overreading keyword-level cues rather than deeper institutional structure."
            ] if parse_humility["analysis_mode"] != "reviewable" else [],
            "should_suspend_judgment": parse_humility["analysis_mode"] == "triage",
        }
        item["detector_lineage"] = infer_detector_lineage(decision, r.agent, r.concerns)
        item.pop("confidence", None)
        round1_dicts.append(item)

    return CouncilRecord(
        meta={
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "decision": decision,
            "program": "ethics-council-lite",
            "risk_appetite": "moderate",
            "advisory_only": True,
            "architecture": "diagnostic hazard analysis, not verdict optimization",
            "ethical_deliberation_algorithm": ETHICAL_DELIBERATION_ALGORITHM,
        },
        round1=round1_dicts,
        synthesis=synthesis,
        risk=asdict(risk),
        parse_humility=parse_humility,
    )
