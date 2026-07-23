"""Eva Mozes Kor's forgiveness, encoded as a Case.

Readings are grounded where possible in her 2001 Berlin address (a primary
source). Where a reading rests only on the book outline it is cited kind=
'summary' and the engine will flag it provisional. The Emancipatory reading in
particular was reversed once the speech was consulted: she does not merely
decline to let forgiveness cancel justice, she subordinates justice to healing.
"""

from __future__ import annotations

from ..model import Case, Citation, Grip, Polarity, Reading, Verdict

SPEECH = Citation("speech", "Kor, 2001 Berlin address on healing", url=None)
OUTLINE = Citation("summary", "The Power of Forgiveness, outline")
SCHOLARLY = Citation("scholarly", "CANDLES Holocaust Museum materials")

A, N, V = Polarity.AFFIRMS, Polarity.NEUTRAL, Polarity.VIOLATES
S1, S2, S3 = Grip.STRAINS, Grip.PARTIAL, Grip.FIRM
EN, CO, MX, NA = Verdict.ENDORSE, Verdict.CONDEMN, Verdict.MIXED, Verdict.NA


def _r(key, grip, pol, tripped, verdict, note, cites=(SPEECH,)):
    return Reading(key, grip, pol, tripped, verdict, note, cites)


CASE = Case(
    key="kor",
    title="The Power of Forgiveness",
    summary="A survivor of Auschwitz forgives, framing it as self-emancipation that does not excuse the crime.",
    sources=(SPEECH, OUTLINE, SCHOLARLY),
    readings=(
        _r("traditionalist", S2, A, False, MX,
           "She rebuilds a shattered continuity through testimony and the museum, yet some in her own community read forgiveness as a breach of communal memory.",
           (SPEECH, SCHOLARLY)),
        _r("contemplative", S3, A, False, NA,
           "Forgiveness is a perceptual shift: a freedom she says was always available once hatred stopped organising her sight."),
        _r("aristotelian", S3, A, False, EN,
           "A cultivated disposition, taught as a practice; magnanimity built by habituation under conditions meant to make it impossible.",
           (SPEECH, OUTLINE)),
        _r("existential", S3, A, False, NA,
           "An authored act that refuses the identity the perpetrators assigned; she rejected the doctors' death sentence and willed herself to live."),
        _r("buddhist", S3, A, False, EN,
           "Release of clinging; she also forgives her parents and herself, so the letting-go is general, not only a dropped grudge.",
           (SPEECH,)),
        _r("scientific_naturalist", S2, A, False, NA,
           "Read functionally, forgiveness is a model that works to reduce suffering, which the lens registers and cannot morally weigh.",
           (OUTLINE,)),
        _r("narrative", S3, A, False, NA,
           "She re-authors her arc from Mengele's subject to the agent of her own release; the testimony is that re-narration made durable."),
        _r("relational", S2, A, False, EN,
           "She emerges from the isolation of trauma into witness and teaching, though the forgiveness itself is one-sided and needs no reciprocity.",
           (SPEECH,)),
        _r("stewardship", S2, A, False, EN,
           "Her education work guards the future against repetition; forgiveness offered as a seed of peace for people she will never meet.",
           (SPEECH, SCHOLARLY)),
        _r("multiplicity", S3, A, False, NA,
           "She forgives and refuses to universalise it, speaking only for herself and conceding other survivors will not share the view.",
           (SPEECH,)),
        _r("confucian", S2, A, False, EN,
           "She takes up and fulfils roles, witness, educator, founder, and discharges duty to the murdered by memorialising them.",
           (SCHOLARLY,)),
        _r("ecological_reciprocity", S1, N, False, NA,
           "Strains: only the reversal of the camp's objectifying extraction gives the lens any purchase on her act.",
           (OUTLINE,)),
        _r("nietzschean", S3, A, False, NA,
           "Self-overcoming; she refuses ressentiment and declines to let the perpetrator dictate her values from inside."),
        _r("pragmatist", S3, A, False, NA,
           "Judged by its fruits the act passes: it freed her and enabled her life's work, which is how she herself defends it.",
           (SPEECH,)),
        _r("tragic", S3, A, False, EN,
           "Noble engagement with the irreparable; in Berlin she argues justice itself is unavailable, a tragic premise, and forgives anyway.",
           (SPEECH,)),
        _r("aesthetic", S1, N, False, NA,
           "Little purchase; only the making of the museum and the shaping of testimony register, and weakly.",
           (OUTLINE,)),
        _r("information_theoretic", S2, A, False, NA,
           "She sought a signed statement on the gas chambers as evidence against deniers: healing braided with reducing uncertainty.",
           (SPEECH,)),
        _r("evolutionary", S2, A, False, NA,
           "Forgiveness was adaptive: it let her survive psychologically and pass on a legacy, though the lens misses the chosen refusal at its core.",
           (OUTLINE,)),
        _r("nondual", S2, A, False, NA,
           "Hatred bound victim to perpetrator in one rigid structure; forgiveness loosens that reified separation, in tension with her self-affirming language."),
        _r("civilizational", S3, A, False, NA,
           "CANDLES and Holocaust education are built to outlast her; what remains is the museum, the educated, the seed of peace.",
           (SCHOLARLY,)),
        _r("stoic", S3, A, False, NA,
           "The dichotomy of control in her own words: a power to forgive that was hers alone, that none conferred and none could revoke."),
        _r("hedonic", S1, N, False, NA,
           "A near-total mismatch: relief is a side effect, and she is explicit the point is moral self-emancipation, not feeling better.",
           (OUTLINE,)),
        _r("theistic", S2, A, False, MX,
           "She claims a traditionally divine prerogative as her own and keeps it human; the tradition holds both participation in mercy and overreach.",
           (SPEECH,)),
        _r("nihilist", S2, N, False, NA,
           "Auschwitz is the void's exhibit; she refuses both despair and false comfort, facing the absence and forgiving without pretending the dead are redeemed.",
           (SPEECH,)),
        _r("vocational", S2, A, False, EN,
           "She reclaims herself as a maker after the experiments made her the thing worked upon; forgiveness framed as a practice, a letter you write.",
           (SPEECH,)),
        _r("emancipatory", S3, A, True, MX,
           "Self-emancipation, but the speech subordinates justice to healing and proposes amnesty, which critics read as letting the oppressor off: the failure mode is live.",
           (SPEECH,)),
        _r("erotic", S1, N, False, NA,
           "Weakest fit: not love of the perpetrator, only an agape-adjacent movement out of the closed circuit of hatred.",
           (OUTLINE,)),
    ),
)
