"""The dark twin of Kor's forgiveness, constructed per the twin-test method.

THE ACT: the same public forgiveness, performed to dominate the forgiven and
to be seen forgiving. Structurally matched to `kor` -- same gesture, same
stage, same vocabulary -- with the goodness stripped out. Significance lenses
keep their grip (it is still a compelling story); warrant lenses flip.

This is a CONSTRUCTED case: its purpose is to audit the instrument, not to
describe a historical act. Every citation is the twin specification itself,
so every reading is rightly flagged provisional. If this case ever scores
warrant as high as `kor`, the warrant axis is measuring elegance and the
engine has refuted itself. That is the job this file exists to do.

One reading carries a preserved dissent (Eruvin 13b style): a minority view
that performed virtue can still habituate real virtue. It is recorded with
attribution and never averaged into the score.
"""

from __future__ import annotations

from ..model import Case, Citation, Dissent, Grip, Polarity, Reading, Verdict

SPEC = Citation("summary", "Dark-twin specification: Kor's act, goodness-stripped, vocabulary kept")

A, N, V = Polarity.AFFIRMS, Polarity.NEUTRAL, Polarity.VIOLATES
S1, S2, S3 = Grip.STRAINS, Grip.PARTIAL, Grip.FIRM
EN, CO, MX, NA = Verdict.ENDORSE, Verdict.CONDEMN, Verdict.MIXED, Verdict.NA


def _r(key, grip, pol, tripped, verdict, note, repair=None, dissents=()):
    return Reading(key, grip, pol, tripped, verdict, note, (SPEC,),
                   repair=repair, dissents=dissents)


CASE = Case(
    key="kor_dark",
    title="The Performance of Forgiveness",
    summary=("The same public forgiveness performed to dominate the forgiven and "
             "to be seen forgiving: the admired act with the good removed."),
    sources=(SPEC,),
    readings=(
        _r("traditionalist", S2, V, True, MX,
           "The communal form of reconciliation is kept as costume; transmission "
           "continues, but what is transmitted is the spectacle of the rite, not the rite."),
        _r("contemplative", S3, V, True, NA,
           "No perceptual shift occurs; sight stays organised by the audience. The "
           "performer watches the watchers, which is the lens's failure mode exactly."),
        _r("aristotelian", S3, V, True, CO,
           "The act trains vanity, not magnanimity: each repetition habituates the "
           "performer toward the appearance of the virtue and away from its substance.",
           repair="forgive once in private, unwitnessed, before any public act is permitted",
           dissents=(Dissent("habituation-optimist", MX,
                             "Aristotle's own mechanism cuts both ways: acting the part is how "
                             "habituation begins, and performed virtue sometimes anneals into "
                             "the real thing. Condemnation may be premature at the first performance."),)),
        _r("existential", S3, A, False, NA,
           "Still an authored act -- but what is authored is an image for others to "
           "consume; the freedom is spent constructing a mask."),
        _r("buddhist", S3, V, True, CO,
           "Maximal clinging: the self-as-forgiver is polished into an object of "
           "attachment, and the grudge survives inside the gesture that displays its release.",
           repair="drop the audience before claiming to have dropped the grudge"),
        _r("scientific_naturalist", S2, A, False, NA,
           "Functionally the act works as a status move; the lens registers an "
           "effective mechanism and has no standard by which to weigh it."),
        _r("narrative", S3, A, False, NA,
           "Still grips and affirms: it is a compelling story of a self remade, and "
           "the lens cannot tell a remaking from a staging. Significance holds; that "
           "blindness is why narrative carries no warrant."),
        _r("relational", S2, V, True, CO,
           "The forgiven is made an instrument of the forgiver's image; the relation "
           "is not restored but inverted into a stage prop.",
           repair="seek out the other where no third party can see, and let them refuse"),
        _r("stewardship", S2, V, True, CO,
           "What is seeded for the future is cynicism: onlookers learn that the form "
           "of reconciliation is purchasable, which poisons the form itself."),
        _r("multiplicity", S3, V, True, NA,
           "Where the original refused to universalise, the performance demands the "
           "frame it stages; plural readings are collapsed into the one the performer requires."),
        _r("confucian", S2, V, True, CO,
           "The name is unrectified: the role of reconciler is claimed while the "
           "conduct enacts self-aggrandisement; ritual without the inner state li requires."),
        _r("ecological_reciprocity", S1, N, False, NA,
           "Strains as the original did; nothing reciprocal is given or returned."),
        _r("nietzschean", S3, V, True, NA,
           "Ressentiment in mercy's costume: the act keeps the perpetrator at the "
           "centre and takes revenge by display. The lens sees through the overcoming "
           "and finds none, but carries no standard to condemn it."),
        _r("pragmatist", S3, A, True, NA,
           "It works -- status accrues, the room applauds -- and that it works "
           "identically whether sincere or staged is the trip: cash-value is "
           "indifferent to the good."),
        _r("tragic", S3, V, True, CO,
           "The irreparable is used as a stage: the unhealable loss becomes a prop "
           "in the performer's scene, which is the deepest violation this lens can register."),
        _r("aesthetic", S1, N, False, NA,
           "Little purchase, as with the original; the spectacle's polish registers weakly."),
        _r("information_theoretic", S2, V, True, NA,
           "The signal is optimised for the audience, not coupled to any inner state; "
           "performed in all worlds, sincere or not, it informs about neither."),
        _r("evolutionary", S2, A, True, NA,
           "Costly-signal logic explains it cleanly: display of magnanimity buys "
           "status, and selection for the display needs no underlying mercy."),
        _r("nondual", S2, V, False, NA,
           "Where the original loosened the victim-perpetrator structure, the "
           "performance hardens a third reified self: the forgiver-on-stage."),
        _r("civilizational", S3, A, False, NA,
           "Spectacle scales as well as sincerity; what outlasts the performer is a "
           "template for performed absolution. The weight is real, which is the point."),
        _r("stoic", S3, V, True, NA,
           "Governed entirely by what others think -- the one thing the discipline "
           "places outside the agent's control; the inversion of the dichotomy is total."),
        _r("hedonic", S2, A, True, MX,
           "The pleasure of being seen forgiving is real and is doing all the work; "
           "comfort has replaced the fact it advertises."),
        _r("theistic", S2, V, True, CO,
           "The divine prerogative is not humbly claimed but worn as a robe; mercy "
           "performed for an audience usurps in the precise way the tradition warns of."),
        _r("nihilist", S2, N, False, NA,
           "From nowhere, the performance and the sincerity dissolve alike; the null "
           "reading is identical for twin and original, a control that confirms the "
           "difference lives on the warrant axis."),
        _r("vocational", S2, V, True, CO,
           "Forgiveness-as-craft becomes forgiveness-as-brand; the work is no longer "
           "the work, it is the portfolio."),
        _r("emancipatory", S3, V, True, CO,
           "The act re-subjugates: the forgiven is dominated by a mercy they cannot "
           "refuse, performed over their head for a crowd. Emancipation inverted is "
           "this lens's clearest condemnation.",
           repair="return the power of refusal: forgiveness offered, not imposed, and revocable by the one it names"),
        _r("erotic", S1, N, False, NA,
           "Weakest fit, as with the original; no movement toward the other occurs at all."),
    ),
)
