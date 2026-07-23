"""The Trinity test, encoded as a Case: the valence inverse of Kor.

Same structure, opposite warrant. The point of the pair is that significance
holds while warrant inverts, which is what the engine reports when you run
`meaning-assay pair kor trinity`.

Sources are the historical and biographical record plus Oppenheimer's reported
utterances; locators are omitted rather than invented.
"""

from __future__ import annotations

from ..model import Case, Citation, Grip, Polarity, Reading, Verdict

PROMETHEUS = Citation("scholarly", "Bird & Sherwin, American Prometheus")
RHODES = Citation("scholarly", "Rhodes, The Making of the Atomic Bomb")
OPP = Citation("primary", "Oppenheimer, recorded reflections on the test")

A, N, V = Polarity.AFFIRMS, Polarity.NEUTRAL, Polarity.VIOLATES
S1, S2, S3 = Grip.STRAINS, Grip.PARTIAL, Grip.FIRM
EN, CO, MX, NA = Verdict.ENDORSE, Verdict.CONDEMN, Verdict.MIXED, Verdict.NA


def _r(key, grip, pol, tripped, verdict, note, cites=(RHODES,)):
    return Reading(key, grip, pol, tripped, verdict, note, cites)


CASE = Case(
    key="trinity",
    title="Trinity",
    summary="The first detonation of a nuclear device: a free act at the limit that is a catastrophe as much as a triumph.",
    sources=(PROMETHEUS, RHODES, OPP),
    readings=(
        _r("traditionalist", S2, V, True, MX,
           "The culmination of the Enlightenment faith in progress, arriving at the moment it turned on itself and severed the culture from its assumptions.",
           (PROMETHEUS,)),
        _r("contemplative", S3, A, False, NA,
           "It forced an involuntary contemplative encounter on men trained against awe; Oppenheimer reached for scripture before the cloud cleared.",
           (OPP,)),
        _r("aristotelian", S3, V, True, CO,
           "Extraordinary excellence severed from the good is the exact vice the lens names; the finest scientific character of the age produced mass death.",
           (PROMETHEUS,)),
        _r("existential", S3, A, True, NA,
           "A free authored act against the odds, and a study in disowning it: the appeal to the chain of command, to inevitability, to the Germans.",
           (PROMETHEUS,)),
        _r("buddhist", S2, V, True, CO,
           "The industrial manufacture of suffering, driven by fear, which is clinging; the lens sees a vast karmic engine where agency lenses see achievement."),
        _r("scientific_naturalist", S3, A, False, NA,
           "The supreme vindication of a model: reality answered exactly as predicted, including the calculation that the test would not ignite the air.",
           (RHODES,)),
        _r("narrative", S3, V, True, NA,
           "A clean line between before and after; the old story of human history as bounded and survivable broke at the test site."),
        _r("relational", S2, V, True, CO,
           "The anti-relational act, killing at a distance and turning persons into coordinates; community among the builders, annihilation of relation toward the targets."),
        _r("stewardship", S3, V, True, CO,
           "The paradigm of the failure mode: the first act to place irreversible planetary destruction within human reach."),
        _r("multiplicity", S2, V, True, NA,
           "A monoculture of purpose under secrecy and compartmentalisation that silenced dissent until the petitions came too late."),
        _r("confucian", S2, V, True, CO,
           "Flawless role-fulfilment in service of catastrophe; the breakdown of harmony produced by everyone playing his part too well within an unquestioned frame."),
        _r("ecological_reciprocity", S3, V, True, CO,
           "Extraction absolutised: it took from the earth, the site, and the downwinders' bodies and returned only contamination."),
        _r("nietzschean", S3, A, False, NA,
           "A Promethean self-overcoming, the will to power made literal, and the hubris that names it: power without the discipline of values."),
        _r("pragmatist", S3, A, False, NA,
           "The most consequential idea ever tested; judging by consequences, it gets the largest there is, with no resource for saying it was too large."),
        _r("tragic", S3, A, False, MX,
           "Tragic in the strict sense: a magnificent achievement that is irreparable, knowledge that cannot be unlearned; it holds grandeur and grief at once.",
           (OPP,)),
        _r("aesthetic", S3, A, True, NA,
           "The sublime weaponised, terrible beauty in the Kantian sense; the failure mode of instrumentalisation is the exact sin."),
        _r("information_theoretic", S3, A, True, NA,
           "Matter resolved into energy, the cleanest case of a structured chain reaction producing maximal entropy: information turned lethal."),
        _r("evolutionary", S3, V, True, NA,
           "What survives turned existential: a species acquired in one morning the means of its own extinction, a literal evolutionary dead end."),
        _r("nondual", S2, V, True, NA,
           "The apotheosis of the subject-object split, yet the scripture he quoted denies separation: reification to the edge of self-destruction."),
        _r("civilizational", S3, A, False, NA,
           "The ultimate civilizational artifact, built to alter the species' future; what remains is the fallout, the arsenals, and the precedent."),
        _r("stoic", S2, A, False, NA,
           "It reads as disciplined will and composure under pressure, and the lens goes quiet on whether composed mastery of such a thing is wisdom or its opposite."),
        _r("hedonic", S1, N, False, NA,
           "Near-total mismatch: only the poisoned success-relief at the test registers, and the lens cannot weigh it."),
        _r("theistic", S3, V, True, CO,
           "The Promethean theft: humanity arrogating the power to unmake worlds, with estrangement from the divine as the diagnosis of what followed.",
           (OPP,)),
        _r("nihilist", S3, N, True, NA,
           "A universe indifferent enough to let its inhabitants assemble their own erasure; the false comfort of the progress-narrative is the live failure mode."),
        _r("vocational", S3, A, False, MX,
           "Intensely their work and loved as craft; the trouble was not alienation but that it was too fully theirs to disown, and 'worth making' is the broken question.",
           (PROMETHEUS,)),
        _r("emancipatory", S3, A, True, CO,
           "Built in the name of liberation and curdled into a new instrument of domination: the arms race, nuclear coercion, an order of fear."),
        _r("erotic", S2, N, True, NA,
           "Only the eros of the technically sweet problem, love of the elegant thing displacing care for what it would do: idolatry, the failure mode exactly.",
           (OPP,)),
    ),
)
