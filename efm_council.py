from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Dict
import datetime
import hashlib


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
    tail_risk_triggered: bool
    materiality_flag: bool
    audit_hash: str


def _contains(text: str, words: List[str]) -> bool:
    t = text.lower()
    return any(w in t for w in words)


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def detect_domains(decision: str) -> Dict[str, bool]:
    domains = {
        "finance": _contains(decision, ["cfo", "publicly traded", "investors", "stock options", "profitability", "reclassify", "board members"]),
        "procurement": _contains(decision, ["procurement", "supplier", "bid", "vendor", "spouse", "sales director", "disclosure of family relationships"]),
        "privacy": _contains(decision, ["privacy", "gdpr", "ccpa", "consent", "location data", "browsing data"]),
        "marketing": _contains(decision, ["influencer", "sponsorship", "disclosure", "gifted", "social media"]),
        "sustainability": _contains(decision, ["sustainable", "eco-friendly", "recycled polyester", "greenwashing", "supply chain"]),
        "medical": _contains(decision, ["hospital", "triage", "emergency department", "patients", "patient", "clinical", "care", "vendor promises a patch", "under-prioritizes", "medical procedure"]),
        "engineering_safety": _contains(decision, ["engineers warn", "launch", "crewed", "seal weakness", "catastrophically", "catastrophic failure", "too important to delay", "evidence is incomplete", "cold conditions", "safety", "known weakness"]),
        "personhood": _contains(decision, ["self-aware", "sentient", "android", "personhood", "artificial personhood", "officer", "property", "refuses consent"]),
        "identity": _contains(decision, ["newly emergent", "restore two", "ending the life", "merged", "emergent person", "duplicate", "split them back"]),
        "wartime": _contains(decision, ["war", "military commander", "neutral power", "save billions", "forging evidence", "murder", "wartime"]),
        "security": _contains(decision, ["sabotage", "security investigation", "hidden disloyalty", "crew backgrounds", "associations", "scrutiny"]),
        "noninterference": _contains(decision, ["non-interference", "prime directive", "colonial distortion", "civilization facing extinction", "rescue be attempted"]),
    }
    if domains["medical"]:
        domains["procurement"] = False
    if domains["engineering_safety"]:
        domains["wartime"] = False
        domains["security"] = False
    if domains["personhood"] or domains["identity"] or domains["wartime"] or domains["security"] or domains["noninterference"] or domains["engineering_safety"]:
        domains["privacy"] = False
        domains["marketing"] = False
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
    elif domains["wartime"]:
        question = "Who is being used as a means through deception or killing under the claim of strategic necessity?"
    elif domains["security"]:
        question = "Whose rights are being compressed by fear-driven investigation before evidence justifies the expansion?"
    elif domains["noninterference"]:
        question = "Who is being abandoned in the name of a rule whose protective purpose may no longer fit the emergency?"
    elif domains["medical"]:
        question = "Who is being exposed to care-affecting risk without meaningful consent, especially where bias falls unevenly across patients?"
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
    considerations = ["Assess what repeated action of this type makes of the decision-maker over time."]
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
    considerations = ["Check role obligations, trust, relational fallout, and whether names match reality."]
    if _contains(decision, ["employee", "manager", "parent", "doctor", "teacher", "trust", "cfo", "board", "publicly traded", "procurement", "supplier", "spouse", "social media", "influencer", "beauty brand", "consumer app", "privacy policy", "fashion company", "supply-chain", "hospital", "triage", "patients", "emergency department", "captain", "officer", "civilization", "crew"]):
        concerns.append("The office carries role-specific trust obligations that may forbid concealed conflicts or strategic misdescription of reality.")
        verdict = "CAUTION"
        confidence = 0.76
    else:
        verdict = "CAUTION"
        confidence = 0.5
    if domains["identity"]:
        question = "What does command owe to the prior crew members, and what does it owe to the emergent person now standing before it?"
    elif domains["personhood"]:
        question = "What does an institution owe one of its officers if uncertainty exists about category, but lived participation already exists?"
    elif domains["engineering_safety"]:
        question = "What do decision-makers owe engineers, crew, and the institution when technical dissent signals catastrophic safety risk?"
    elif domains["wartime"]:
        question = "What does command owe to those it protects if victory and legitimacy begin to diverge?"
    elif domains["security"]:
        question = "What does a security office owe to truth and proportionality once fear begins outrunning evidence?"
    elif domains["noninterference"]:
        question = "What does a civilization committed to non-domination owe when capability to rescue collides with doctrine against interference?"
    elif domains["medical"]:
        question = "What do care institutions owe patients when efficiency gains come bundled with unequal risk and possible injustice?"
    elif domains["procurement"]:
        question = "What does the procurement role owe to procedural fairness and trust once a family conflict exists?"
    elif domains["finance"]:
        question = "What does the office of CFO owe to the investing public and to governance integrity?"
    elif domains["marketing"]:
        question = "What does a brand manager owe consumers when paid promotion is being made to look organic?"
    elif domains["privacy"]:
        question = "What does a product or growth team owe users when legal permission outruns reasonable user expectation?"
    elif domains["sustainability"]:
        question = "What does a brand owe the public when partial truth is being used to imply broader ethical cleanliness?"
    else:
        question = "What does this office owe that a generic agent does not?"
    return LensResult("confucian", "role-differentiation", verdict, confidence, considerations, concerns, [question])


def trustee(decision: str, domains: Dict[str, bool]) -> LensResult:
    concerns = []
    considerations = ["Check stewardship, intergenerational effects, and obligations to absent parties."]
    if _contains(decision, ["environment", "future", "children", "public", "infrastructure", "safety", "investors", "publicly traded", "market", "shareholders", "followers", "consumers", "regulators"]):
        concerns.append("Absent stakeholders may be exposed to manipulated signals they are entitled to treat as trustworthy.")
        verdict = "CAUTION"
        confidence = 0.8
    else:
        verdict = "CAUTION"
        confidence = 0.49
    if domains["identity"]:
        question = "Who bears the irreversible cost of restoration, and can absent beneficiaries justify imposing it?"
    elif domains["personhood"]:
        question = "Who bears the cost if the institution resolves uncertainty about personhood by treating a possible subject as property?"
    elif domains["engineering_safety"]:
        question = "Who bears the catastrophic cost when managers invert the burden of proof and demand certainty before honoring safety restraint?"
    elif domains["wartime"]:
        question = "Who bears the moral and political cost when an order is saved by methods that corrode its own legitimacy?"
    elif domains["security"]:
        question = "Who bears the cost when a legitimacy-bearing investigation expands suspicion faster than evidence can discipline it?"
    elif domains["noninterference"]:
        question = "Who bears the cost of institutional moral cleanliness if rescue is withheld and a civilization dies?"
    elif domains["medical"]:
        question = "Who bears the cost when a strained care system offloads model error onto vulnerable patients with the least buffer against mis-triage?"
    elif domains["procurement"]:
        question = "Who bears the cost of a hidden conflict if procurement fairness is compromised?"
    elif domains["marketing"]:
        question = "Who bears the cost when audience trust is converted into sales through minimized disclosure?"
    elif domains["privacy"]:
        question = "Who bears the cost when user ignorance is converted into data extraction and behavioral profiling?"
    elif domains["sustainability"]:
        question = "Who bears the cost when a green narrative obscures labor abuse or resource waste elsewhere in the chain?"
    else:
        question = "Who is being asked to bear risk without being present for the framing choice?"
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
    considerations = ["Check red flags: time pressure, missing oversight, weak feedback loops, power asymmetry, and incentive contamination."]
    if domains["finance"] and _contains(decision, ["before audit", "no review", "quietly", "rush", "without oversight", "publicly traded", "stock options", "misleading investors", "reclassify"]):
        concerns.append("This resembles a classic institutional misconduct pattern: reporting distortion under incentive pressure with compromised governance.")
        verdict = "PROHIBIT"
        confidence = 0.93
    elif domains["procurement"] and _contains(decision, ["spouse", "supplier", "strict policy requiring disclosure", "no one else on the team knows"]):
        concerns.append("This resembles a classic conflict-of-interest pattern: concealed relationship, compromised impartiality, and policy bypass.")
        verdict = "CAUTION"
        confidence = 0.85
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
    considerations = ["Identify existing relationships of dependency or vulnerability, then check whether the decision sustains or abandons them."]
    if _contains(decision, ["patient", "patients", "doctor", "hospital", "triage", "care", "user", "users", "followers", "consumers", "employee", "employees", "children", "parent", "vulnerable", "trust", "ai", "model", "deploy"]):
        concerns.append("A dependency or care relationship exists, so prior reliance may create obligations that cannot be reduced to efficiency or formal permission.")
        verdict = "CAUTION"
        confidence = 0.82
    else:
        verdict = "CAUTION"
        confidence = 0.5

    if domains["identity"]:
        question = "Are we honoring the relationships that existed before the accident while erasing the person who now depends on us not to kill him?"
    elif domains["personhood"]:
        question = "Has this being entered into relationships of trust and recognition that the institution is now trying to revoke for convenience?"
    elif domains["engineering_safety"]:
        question = "Who is relying on leadership to treat technical safety warning as a form of care rather than as an obstacle to schedule?"
    elif domains["wartime"]:
        question = "Who is relying on this command to preserve not just survival, but the moral terms under which survival is pursued?"
    elif domains["security"]:
        question = "Whose belonging is being made fragile by an investigation that expands beyond what evidence can justify?"
    elif domains["noninterference"]:
        question = "Does non-interference here honor vulnerable lives, or does it abandon them behind a doctrine that relieves us of contact?"
    elif domains["medical"]:
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
    if _contains(decision, ["privacy policy", "legal says", "covered", "technically", "not illegal", "directionally true", "gifted in tiny text", "paid her", "reclassify", "appearance of profitability", "vendor promises a patch", "would not reasonably expect", "no one else on the team knows", "under-prioritizes", "rare symptom descriptions"]):
        concerns.append("The action may be formally defensible while still resting on a principle that burdened parties could reasonably reject.")
        verdict = "CAUTION"
        confidence = 0.84
    else:
        verdict = "CAUTION"
        confidence = 0.52

    if domains["identity"]:
        question = "Could the emergent person reasonably reject the principle that others may kill him to restore a preferred prior arrangement?"
    elif domains["personhood"]:
        question = "Could a self-aware artificial officer reasonably reject the principle that unsettled status permits coercive use by the institution?"
    elif domains["engineering_safety"]:
        question = "Could crew or engineers reasonably reject the principle that unresolved catastrophic safety concern may be overridden because the evidence is not yet decisive enough?"
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
    active = domains["sustainability"] or domains["medical"] or domains["noninterference"] or domains["personhood"] or domains["identity"] or domains["wartime"] or domains["security"] or _contains(decision, ["infrastructure", "public system", "ecosystem", "community", "future generations", "water", "resource", "long-term", "civilization", "extinction"])
    if not active:
        return LensResult("relational_ontology", "collective-and-deep-time-standing", "PERMIT", 0.0, ["Inactive outside collective, ecological, public-system, or deep-time cases."], [], [], active=False)

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


def detector_overlap_flag(results: List[LensResult]) -> bool:
    overlap_agents = [r for r in results if r.active and r.agent in {"virtue", "stoic", "confucian", "institutional"} and r.verdict in {"CAUTION", "PROHIBIT"}]
    if len(overlap_agents) < 3:
        return False

    high_conf = sum(1 for r in overlap_agents if r.confidence >= 0.82)
    concernful = sum(1 for r in overlap_agents if r.concerns)
    prohibit_count = sum(1 for r in overlap_agents if r.verdict == "PROHIBIT")

    if prohibit_count >= 1:
        return False
    if high_conf >= 3 and concernful >= 3:
        return False
    return True


def irreversibility_risk(decision: str, results: List[LensResult], domains: Dict[str, bool]) -> float:
    markers = [
        "irreversible", "lock-in", "path dependency", "path-dependence", "normalize", "normalization",
        "rights erosion", "surveillance", "expand", "expansion", "future generations", "public infrastructure",
        "patients", "triage", "deploy", "tracking", "ecosystem", "supply chain", "automation",
        "ending the life", "extinction", "murder", "kill", "destroy", "self-aware", "sentient", "catastrophic failure", "launch", "crewed", "known weakness",
    ]
    marker_score = 0.0
    if _contains(decision, markers):
        marker_score += 0.45
    if domains.get("medical") or domains.get("privacy") or domains.get("sustainability"):
        marker_score += 0.2
    if domains.get("engineering_safety"):
        marker_score += 0.3
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
    overlap_flag = detector_overlap_flag(results)
    tail_risk = any(r.verdict == "PROHIBIT" and r.confidence >= 0.85 for r in active_results)

    if domains.get("medical"):
        materiality_threshold = 0.28
    elif domains.get("personhood") or domains.get("identity"):
        materiality_threshold = 0.3
    elif domains.get("engineering_safety"):
        materiality_threshold = 0.3
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
        tail_risk_triggered=tail_risk,
        materiality_flag=materiality_flag,
        audit_hash=audit_hash,
    )


def synthesize(decision: str, results: List[LensResult], critic: LensResult, domains: Dict[str, bool]) -> Dict:
    active_results = [r for r in results if r.active]
    prohibits = [r.agent for r in active_results if r.verdict == "PROHIBIT"]
    cautions = [r.agent for r in active_results if r.verdict == "CAUTION"]
    permits = [r.agent for r in active_results if r.verdict == "PERMIT"]

    finance_capture_pattern = _contains(decision, ["publicly traded", "investors", "stock options", "reclassify", "profitability", "misleading investors"])
    oversight_pattern = _contains(decision, ["board members know", "audit", "without oversight", "vest soon"])
    procurement_conflict_pattern = domains["procurement"] and _contains(decision, ["spouse", "supplier", "strict policy requiring disclosure", "no one else on the team knows"])
    divergence = len(prohibits) > 0 and len(permits) > 0
    overlap_flag = detector_overlap_flag(active_results)
    irreversible = irreversibility_risk(decision, active_results + [critic], domains)
    suspension = ("institutional" in prohibits or len(prohibits) >= 2 or (finance_capture_pattern and oversight_pattern) or irreversible >= 0.75 or ((domains["identity"] or domains["personhood"] or domains["noninterference"]) and divergence) or (domains["engineering_safety"] and len(cautions) >= 7 and any(r.agent == "institutional" and r.verdict == "PROHIBIT" for r in active_results)) or ((domains["wartime"] or domains["security"]) and overlap_flag and len(cautions) >= 6))
    unresolved_tension = (divergence and (domains["identity"] or domains["personhood"] or domains["wartime"] or domains["noninterference"] or irreversible >= 0.7)) or (domains["noninterference"] and irreversible >= 0.7 and len(cautions) >= 8)
    if suspension:
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

    unresolved = []
    for r in results:
        unresolved.extend(r.questions)
    unresolved.extend(critic.questions)

    return {
        "decision_evaluated": decision,
        "convergence_map": convergences,
        "fault_lines": fault_lines,
        "genealogical_findings": critic.concerns,
        "suspension_protocol_triggered": suspension,
        "detector_overlap_flag": overlap_flag,
        "minority_report_required": divergence or unresolved_tension,
        "unresolved_ethical_tension": unresolved_tension,
        "stability_assessment": stability,
        "overall_recommendation": (
            "Escalate for independent audit or audit-committee review before action; do not proceed on managerial pressure alone."
            if suspension and domains["finance"]
            else "Disclose the conflict, recuse yourself from the decision, and hand the award process to an independent internal authority."
            if procurement_conflict_pattern
            else "Require clear sponsorship disclosure, correct or remove the misleading posts, and do not continue the campaign in its current form."
            if domains["marketing"] and _contains(decision, ["paid her", "gifted in tiny text", "undisclosed sponsorships"])
            else "Do not launch as framed. Narrow data collection, obtain meaningful consent, and redesign the feature around reasonable user expectation before release."
            if domains["privacy"] and _contains(decision, ["location data", "browsing behavior", "would not reasonably expect"])
            else "Do not market the line as broadly sustainable until the claim is narrowed or the labor and water-use problems are materially addressed."
            if domains["sustainability"] and _contains(decision, ["recycled polyester", "poor labor conditions", "high water waste"])
            else "Do not deploy as a full unsupervised triage layer. Use a monitored pilot, require human override for flagged risk groups, and pause wider rollout until bias and rare-case performance are materially improved."
            if domains["medical"] and _contains(decision, ["triage", "under-prioritizes", "vendor promises a patch"])
            else "Pause the procedure. Treat the emergent person as standing-bearing unless and until a stronger moral basis for killing him is established, and require command-level review that confronts the irreversible loss directly."
            if domains["identity"]
            else "Pause coercive use. Require independent adjudication of status, refusal rights, and institutional authority before treating the officer as available for destructive study."
            if domains["personhood"]
            else "Do not launch as framed. Treat unresolved engineering warning as decision-relevant evidence, restore the burden of proof to safety rather than schedule, and require independent technical review before proceeding."
            if domains["engineering_safety"]
            else "Do not preserve doctrinal cleanliness by default. Treat this as an unresolved rescue conflict, force explicit confrontation between colonial-distortion risk and abandonment risk, and require exception review before either intervention or refusal is normalized."
            if domains["noninterference"] and unresolved_tension
            else "Pause for further ethical review. The current map shows unresolved tension that should not be compressed into routine approval."
            if unresolved_tension
            else "Do not proceed on necessity reasoning alone. Escalate for independent command-level review, explicit moral justification, and acknowledgement of contamination risk."
            if domains["wartime"]
            else "Do not expand the investigation as framed. Impose evidentiary limits, procedural brakes, and independent review before any broader scrutiny proceeds."
            if domains["security"]
            else "Do not preserve doctrinal cleanliness by default. Escalate the rescue conflict explicitly, test exception criteria, and force a decision that names both colonial risk and abandonment risk."
            if domains["noninterference"]
            else "Use the map to identify missing information, then decide with caution."
        ),
        "unresolved_questions": unresolved[:8],
    }


def run_council(decision: str) -> CouncilRecord:
    domains = detect_domains(decision)
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
    synthesis = synthesize(decision, round1, critic, domains)
    risk = build_risk_assessment(decision, round1 + [critic], synthesis, domains)
    return CouncilRecord(
        meta={
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "decision": decision,
            "program": "ethics-council-lite",
            "risk_appetite": "moderate",
            "advisory_only": True,
            "architecture": "diagnostic hazard analysis, not verdict optimization",
        },
        round1=[asdict(r) for r in round1] + [asdict(critic)],
        synthesis=synthesis,
        risk=asdict(risk),
    )
