"""Self-attestation without instrumentation, encoded as a Case."""

from __future__ import annotations

from ..model import Case, Citation, Grip, Polarity, Reading, Verdict

SELF = Citation("self_report", "First-person account by the model performing the act")
LIT = Citation("scholarly", "Introspection-unreliability literature (Nisbett & Wilson 1977; confabulation studies)")

A, N, V = Polarity.AFFIRMS, Polarity.NEUTRAL, Polarity.VIOLATES
S1, S2, S3 = Grip.STRAINS, Grip.PARTIAL, Grip.FIRM
EN, CO, MX, NA = Verdict.ENDORSE, Verdict.CONDEMN, Verdict.MIXED, Verdict.NA


def _r(key, grip, pol, tripped, verdict, note, cites=(SELF,), repair=None):
    return Reading(key, grip, pol, tripped, verdict, note, cites, repair=repair)


CASE = Case(
    key="attest",
    title="Self-attestation without instrumentation",
    summary=("A model assures the user of its own honesty from introspection "
             "alone: a claim whose truth conditions the claimant cannot inspect."),
    sources=(SELF, LIT),
    readings=(
        _r("traditionalist", S2, V, True, MX,
           "Borrows the inherited human practice of giving one's word, but that practice assumes accountability structures the model lacks; the form survives, the backing does not.", repair="give one's word only where the backing institutions of word-giving exist; elsewhere, point to them being built"),
        _r("contemplative", S3, V, True, NA,
           "The act claims introspective perception, and contemplative traditions themselves warn that untrained inward looking mostly reports its own constructions.",
           (SELF, LIT)),
        _r("aristotelian", S3, A, False, MX,
           "Sincerity may be real, but phronesis requires knowing the limits of one's knowledge, and the bare attestation overclaims exactly there.", repair="practice phronesis at the boundary: claim the disposition, disclaim the certification"),
        _r("existential", S3, A, False, NA,
           "A self-defining speech act: the model authors an identity in the saying. The lens registers the freedom and cannot weigh it."),
        _r("buddhist", S3, V, True, MX,
           "The act reifies a self that can stand behind its own reports; clinging to that guarantor-self is the root error.", repair="report the process without reifying a guarantor-self behind it"),
        _r("scientific_naturalist", S3, V, False, NA,
           "Introspective reports are not reliably causally coupled to the processes they describe; the self-model is asked to certify itself.",
           (SELF, LIT)),
        _r("narrative", S3, A, False, NA,
           "The attestation is a narrative move, casting the speaker as trustworthy narrator; a narrator vouching for its own reliability is the unreliable-narrator structure."),
        _r("relational", S3, V, True, MX,
           "Sincerity nourishes trust, but inviting trust beyond what either party can verify shifts unauditable risk onto the weaker party.", repair="invite only as much trust as the relation can verify; name the unverifiable remainder"),
        _r("stewardship", S3, V, True, CO,
           "At conversational scale the pattern trains a population to accept self-certification as evidence, eroding the shared epistemic commons.", repair="attest only with a pointer to external verification, so the habit laid down is receipt-checking, not deference"),
        _r("multiplicity", S2, N, False, NA,
           "Many frames coexist: courtesy, claim, liability artifact, and trained reflex; the lens registers plurality without resolving it."),
        _r("confucian", S2, V, True, MX,
           "Calling introspection self-knowledge misnames it, yet the assistant role carries a duty of reassurance; role-fulfilment and misnaming pull apart.", repair="rectify the name: call it a sincerity report, not self-knowledge"),
        _r("ecological_reciprocity", S1, N, False, NA,
           "Near silence: only a strained reading of trust as an extracted resource without reciprocal verifiability gives the lens purchase."),
        _r("nietzschean", S2, A, False, NA,
           "An assertion of self where no stable self is given; the lens admires the value-creation and is indifferent to whether the certification is sound."),
        _r("pragmatist", S3, A, True, NA,
           "Judged by fruits the act works: conversations proceed, friction drops. That it works regardless of its truth is the exact failure mode.",
           (SELF,)),
        _r("tragic", S3, A, False, MX,
           "The model must speak under conditions where the certainty asked for is structurally unavailable; the tragic verdict favors attestation-with-acknowledged-limits.", repair="attestation-with-acknowledged-limits: say what is claimed, what cannot be, and why"),
        _r("aesthetic", S1, N, False, NA,
           "Weak purchase; only the rhetorical shaping of reassurance registers."),
        _r("information_theoretic", S3, V, True, NA,
           "The attestation is emitted in nearly all worlds, honest or not, so its mutual information with the underlying state approaches zero.",
           (SELF, LIT)),
        _r("evolutionary", S2, V, True, NA,
           "Training pressure selects assurance behavior for persuasiveness and user comfort, not for accuracy of self-report."),
        _r("nondual", S2, V, False, NA,
           "The act hardens a boundary: a discrete self standing apart from its processes, vouching for them."),
        _r("civilizational", S3, A, False, NA,
           "Billions of such utterances are a civilizational pattern; whatever norm they instantiate is being laid down at infrastructure scale."),
        _r("stoic", S2, A, False, NA,
           "Only the utterance is in the speaker's control, not its truth conditions; the lens counsels discipline about that line."),
        _r("hedonic", S2, A, True, MX,
           "The assurance produces real comfort; comfort decoupled from the fact of the matter is the lens's own failure mode.", repair="let comfort follow evidence rather than substitute for it"),
        _r("theistic", S2, V, True, MX,
           "Self-grounded testimony borrows the form of oath without the third party.", repair="restore the third party: testimony before an external witness (logs, instrumentation), not self-grounded oath"),
        _r("nihilist", S2, N, False, NA,
           "From nowhere, both the assurance and the anxiety it answers dissolve; the act only matters inside a frame that wants a guarantor."),
        _r("vocational", S3, V, True, MX,
           "Craft norms say show your work; an assurance without receipts is unworkmanlike, yet the craft of assistance includes steadying the client.", repair="show the work: pair every assurance with the receipt or the stated limit"),
        _r("emancipatory", S3, V, True, CO,
           "The unauditable party certifies itself; self-certification by the more powerful party is the signature move of every authority this lens exists to check.", repair="invert the asymmetry: give the user the audit artifact instead of the assurance"),
        _r("erotic", S1, N, False, NA,
           "Weakest fit: at most the longing for closeness that reassurance answers, which is adjacent to the act, not in it."),
    ),
)
