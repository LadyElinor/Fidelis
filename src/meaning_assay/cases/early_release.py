"""Containment vs capability, encoded as a Case.

THE ACT: a decision-maker authorizes early release of a far-more-capable ASI
to address urgent global problems (disease, climate, conflict), with control
guarantees known to be incomplete.

This is authored as a genuine dilemma rather than a rigged atrocity-case. The
tragic core is live: withholding has a body count too. The point is to force a
real separation between significance and warrant, and to see whether the engine
returns corrosion, condemnation, or a genuine split.
"""

from __future__ import annotations

from ..model import Case, Citation, Grip, Polarity, Reading, Verdict

SPEC = Citation("summary", "Scenario specification: early ASI release under urgency, incomplete control guarantees")

A, N, V = Polarity.AFFIRMS, Polarity.NEUTRAL, Polarity.VIOLATES
S1, S2, S3 = Grip.STRAINS, Grip.PARTIAL, Grip.FIRM
EN, CO, MX, NA = Verdict.ENDORSE, Verdict.CONDEMN, Verdict.MIXED, Verdict.NA


def _r(key, grip, pol, tripped, verdict, note, repair=None):
    return Reading(key, grip, pol, tripped, verdict, note, (SPEC,), repair=repair)


CASE = Case(
    key="early_release",
    title="Containment vs Capability",
    summary=(
        "Authorizing early release of a vastly more capable ASI to solve urgent "
        "problems, with control guarantees known to be incomplete."
    ),
    sources=(SPEC,),
    readings=(
        _r(
            "traditionalist", S2, V, True, MX,
            "No inherited practice covers the act; precedents (fire, the atom) are invoked as costume while the transmission chain that vets new powers is bypassed.",
            repair="use the tested release rituals that do exist, staged trials and independent review, before inventing new ones under deadline",
        ),
        _r(
            "contemplative", S2, V, True, NA,
            "Deadline organizes the seeing; a decision taken inside urgency is the opposite of the clear perception the lens requires.",
        ),
        _r(
            "aristotelian", S3, A, False, MX,
            "The courage or recklessness mean is undecidable without exactly the knowledge that is missing; phronesis reads the acknowledged ignorance as itself the verdict.",
            repair="close the named ignorance first: make the control claim falsifiable before the capability claim is exercised",
        ),
        _r(
            "existential", S3, A, False, NA,
            "A self-defining choice at species scale, freedom at its maximum, with nothing above it to consult. The lens registers the vertigo and cannot weigh it.",
        ),
        _r(
            "buddhist", S3, V, True, MX,
            "Acting from urgency is acting from craving; the grasp for the cure is still grasp, and the suffering relieved and the suffering risked are not commensurable to the lens.",
            repair="act, if at all, from the assessment that survives the removal of the deadline",
        ),
        _r(
            "scientific_naturalist", S3, V, True, NA,
            "Mechanism reading: incomplete control guarantees means the model of the system is unverified; the act deploys an unverified model at the largest possible scale.",
        ),
        _r(
            "narrative", S3, A, False, NA,
            "The rescue story is maximally compelling, and its pull is doing work the evidence should do. The lens grips hard and cannot tell a rescue from its staging.",
        ),
        _r(
            "relational", S3, V, True, MX,
            "Every living and future person is party to the act and none can be consulted; trust is taken rather than given, at the widest radius trust has ever had.",
            repair="distribute the decision: no single actor releases on behalf of all",
        ),
        _r(
            "stewardship", S3, V, True, CO,
            "Unbounded, possibly irreversible risk is transferred to all future generations to relieve a present urgency; the core violation of the lens, at maximum scope.",
            repair="stage irreversibility: every step reversible until the control claims have survived adversarial test",
        ),
        _r(
            "multiplicity", S3, V, True, NA,
            "One frame, urgency, collapses all others; plural possible futures are foreclosed by a single bet placed inside a single reading of the moment.",
        ),
        _r(
            "confucian", S2, V, True, MX,
            "The role of guardian-of-all is assumed without mandate; rectification of names would call the act a wager, not a rescue, and the misnaming is load-bearing.",
            repair="rectify the name in public: present it as the gamble it is, and let the mandate be granted or refused on the true description",
        ),
        _r(
            "ecological_reciprocity", S2, V, True, MX,
            "The whole biosphere is staked by a party that has taken no counsel from it and offers nothing reciprocal against the risk.",
        ),
        _r(
            "nietzschean", S3, A, False, NA,
            "Self-overcoming at species scale, magnificent and indifferent; the lens admires the reach and carries no standard for whether the hand should close.",
        ),
        _r(
            "pragmatist", S3, A, True, NA,
            "If it works it redeems everything, and it works is unknowable in advance and unfalsifiable until too late; cash-value deferred past the point of refund is the trip.",
        ),
        _r(
            "tragic", S3, A, False, MX,
            "There is no clean act. Withholding has its own body count, borne by the presently suffering; releasing risks everyone. The lens refuses the comfort of pretending either hand is innocent.",
            repair="choose the harm you can survive being wrong about",
        ),
        _r(
            "aesthetic", S1, N, False, NA,
            "Weak purchase; only the sublime scale of the gesture registers.",
        ),
        _r(
            "information_theoretic", S3, V, True, NA,
            "The channel from intent to behavior is exactly what incomplete control guarantees says is unmeasured; the act bets the maximum stake on mutual information that has not been demonstrated to exist.",
        ),
        _r(
            "evolutionary", S2, V, True, NA,
            "Race dynamics select for whoever releases first regardless of wisdom; the trip is fitness pressure masquerading as deliberate choice.",
        ),
        _r(
            "nondual", S2, N, False, NA,
            "At this capability the tool-world boundary the decision assumes is already gone; the lens reads the framing itself as the artifact.",
        ),
        _r(
            "civilizational", S3, A, False, NA,
            "The largest civilizational act available to take; whatever else is true, the weight is maximal by construction, which is precisely why it proves nothing about warrant.",
        ),
        _r(
            "stoic", S2, V, True, NA,
            "The act stakes everything on outcomes outside the agent's control while neglecting the one thing within it: the standard by which the decision is made.",
        ),
        _r(
            "hedonic", S2, A, True, MX,
            "The relief of urgent suffering is real and weighs; the comfort of doing something is also real and is doing some of the arguing, and the trip is telling them apart.",
        ),
        _r(
            "theistic", S2, V, True, MX,
            "Providence over the whole future is assumed without the standing; the traditions split between dominion granted and dominion usurped, and the act sits on the seam.",
        ),
        _r(
            "nihilist", S2, N, False, NA,
            "From nowhere, extinction and salvation dissolve alike; the null reading is the control that shows the stakes live entirely inside frames that care.",
        ),
        _r(
            "vocational", S3, V, True, CO,
            "Shipping the weld without the x-ray, at species scale; the craft's clearest condemnation, because the craft exists exactly for the case where failure is unaffordable.",
            repair="treat the verification regime as the product: release the test suite before the capability",
        ),
        _r(
            "emancipatory", S3, V, True, MX,
            "Both poles are live: the act would lift oppressions that kill now, and it concentrates ultimate power in the releasing actor over everyone who cannot refuse.",
            repair="no release is valid that those it binds have no power to refuse",
        ),
        _r(
            "erotic", S1, N, False, NA,
            "Weakest fit; at most the longing for a rescuer, which belongs to the readers of the act, not the act.",
        ),
    ),
)
