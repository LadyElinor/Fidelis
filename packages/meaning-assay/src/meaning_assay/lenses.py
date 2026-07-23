"""The lensbook: twenty-seven traditions of meaning as data.

Function tags are analytical claims, not facts. They are placed here, in the
open, with a one-line rationale each, precisely so they can be argued with and
revised. The decision rule used for the WARRANT tag is strict:

    A tradition is tagged WARRANT iff it supplies a standard by which the ACT
    ITSELF can be judged morally better or worse -- not merely a standard for
    the agent's inner state, and not merely an epistemic or instrumental
    standard ("does the model predict", "does it work").

That rule is why Stoic is SIGNIFICANCE-only here: its virtue standard is
agent-directed (was the actor composed, rational?) and does not deliver a
verdict on the external act, which is exactly how it behaved on the Trinity
case. Likewise Pragmatist and Scientific Naturalist carry standards that are
instrumental/epistemic rather than moral, so they are MECHANISM, not WARRANT.
"""

from __future__ import annotations

from .model import Function, Tradition

S = Function.SIGNIFICANCE
W = Function.WARRANT
M = Function.MECHANISM

LENSBOOK: tuple[Tradition, ...] = (
    Tradition(
        "I", "traditionalist", "Traditionalist",
        "What larger story am I serving?",
        "Meaning is inherited; the self is a participant in orders larger than itself.",
        "Rootlessness.",
        ("T. S. Eliot", "Edmund Burke"),
        frozenset({S, W}),
        "Locates meaning in inherited order (significance) and that order prescribes norms for acts (warrant).",
    ),
    Tradition(
        "II", "contemplative", "Contemplative",
        "What is present that I fail to perceive?",
        "Ordinary consciousness obscures a reality that direct awareness can recover.",
        "Conceptual imprisonment.",
        ("Meister Eckhart", "Aldous Huxley"),
        frozenset({S}),
        "Concerns the perception of what matters; supplies no standard for judging an external act.",
    ),
    Tradition(
        "III", "aristotelian", "Aristotelian",
        "What kind of person am I becoming?",
        "Meaning is the cultivation of capacity into virtue, ordered to a good end.",
        "Vice; the corruption of a capacity.",
        ("Aristotle", "Thomas Aquinas"),
        frozenset({S, W}),
        "Flourishing locates significance; virtue ordered to the good is a standard for acts.",
    ),
    Tradition(
        "IV", "existential", "Existential",
        "What am I willing to choose?",
        "Meaning is authored by radical choice; existence precedes essence.",
        "Bad faith.",
        ("Jean-Paul Sartre", "Albert Camus", "Simone de Beauvoir"),
        frozenset({S}),
        "Pure agency; explicitly refuses any given standard of the good, so it cannot judge the act.",
    ),
    Tradition(
        "V", "buddhist", "Buddhist",
        "What suffering can be understood and relieved?",
        "Suffering arises from clinging; meaning is release toward liberation.",
        "Clinging.",
        ("Sakyamuni Buddha", "Nagarjuna"),
        frozenset({S, W}),
        "Liberation from suffering locates significance; non-harm and compassion judge acts.",
    ),
    Tradition(
        "VI", "scientific_naturalist", "Scientific Naturalist",
        "Does this help us understand reality?",
        "Meaning is functional; interpretations are tested by explanatory and predictive power.",
        "False models.",
        ("Carl Sagan", "Daniel Dennett"),
        frozenset({M}),
        "Its standard is epistemic (does the model hold), not moral; describes rather than judges or locates.",
    ),
    Tradition(
        "VII", "narrative", "Narrative",
        "What story am I living?",
        "The self is interpreted narratively; identity depends on continuity across time.",
        "Narrative collapse.",
        ("Paul Ricoeur", "Alasdair MacIntyre"),
        frozenset({S, M}),
        "Emplotment is a structural property (mechanism) that also confers mattering (significance).",
    ),
    Tradition(
        "VIII", "relational", "Relational",
        "Who is transformed by my presence?",
        "The self becomes itself through relationships of recognition and care.",
        "Isolation.",
        ("Martin Buber", "Emmanuel Levinas"),
        frozenset({S, W}),
        "Meaning between persons locates significance; care and recognition are a standard for acts.",
    ),
    Tradition(
        "IX", "stewardship", "Stewardship",
        "What future possibilities am I protecting?",
        "Acts are measured by their effect on future flourishing and resilience.",
        "Irreversible destruction.",
        ("Hans Jonas", "Aldo Leopold"),
        frozenset({S, W}),
        "Future flourishing both locates significance and is a standard for judging acts.",
    ),
    Tradition(
        "X", "multiplicity", "Multiplicity",
        "What becomes visible only when perspectives remain plural?",
        "Reality exceeds any single framework; understanding grows through plural perspectives.",
        "Ideological closure.",
        ("Isaiah Berlin",),
        frozenset({M}),
        "A meta-stance about the structure of understanding; supplies neither a locus of meaning nor a good.",
    ),
    Tradition(
        "XI", "confucian", "Confucian",
        "Am I fulfilling my role well?",
        "Meaning is realised through cultivated relationships, roles, and propriety.",
        "Breakdown of harmony.",
        ("Confucius", "Mencius"),
        frozenset({S, W}),
        "Roles locate significance; propriety and harmony are a standard for judging conduct.",
    ),
    Tradition(
        "XII", "ecological_reciprocity", "Ecological Reciprocity",
        "How do I reciprocate with the living world?",
        "Humans are members, not managers, of a living web of kinship.",
        "Extraction.",
        ("Robin Wall Kimmerer", "Aldo Leopold"),
        frozenset({S, W}),
        "Membership locates significance; reciprocity versus extraction is a standard for acts.",
    ),
    Tradition(
        "XIII", "nietzschean", "Nietzschean",
        "What can I become?",
        "Meaning is self-overcoming and the creation of values.",
        "Ressentiment and stagnation.",
        ("Friedrich Nietzsche",),
        frozenset({S}),
        "Self-overcoming locates significance; explicitly 'beyond good and evil', so it supplies no act-warrant.",
    ),
    Tradition(
        "XIV", "pragmatist", "Pragmatist",
        "What difference does this belief make?",
        "Ideas derive significance from their practical effects.",
        "Sterile abstraction.",
        ("William James", "John Dewey", "C. S. Peirce"),
        frozenset({S, M}),
        "Effect confers significance and is a structural test, but the standard is instrumental, not a good; no robust act-warrant.",
    ),
    Tradition(
        "XV", "tragic", "Tragic",
        "What must be sacrificed?",
        "Meaning emerges through noble engagement with irresolvable conflict.",
        "Denial of tragedy.",
        ("Sophocles", "Miguel de Unamuno"),
        frozenset({S, W}),
        "Recognises real, irreparable loss of the good, which is both a source of weight and a standard for naming catastrophe.",
    ),
    Tradition(
        "XVI", "aesthetic", "Aesthetic",
        "What awakens wonder?",
        "The value of experience is not reducible to utility; beauty and play matter.",
        "Instrumentalization.",
        ("Friedrich Schiller", "Oscar Wilde"),
        frozenset({S, M}),
        "Wonder confers significance and is a property of experience; carries no moral standard (it can find a weapon sublime).",
    ),
    Tradition(
        "XVII", "information_theoretic", "Information-Theoretic",
        "What distinctions become possible?",
        "Meaning emerges through pattern formation and the reduction of uncertainty.",
        "Noise and entropy.",
        ("Claude Shannon", "Norbert Wiener"),
        frozenset({M}),
        "Purely structural; describes form and distinction without locating significance or supplying a good.",
    ),
    Tradition(
        "XVIII", "evolutionary", "Evolutionary",
        "What survives?",
        "Significance is measured through persistence and reproduction.",
        "Dead ends.",
        ("Charles Darwin", "Richard Dawkins"),
        frozenset({M}),
        "Describes persistence; survival is mute on the good, so mechanism rather than warrant.",
    ),
    Tradition(
        "XIX", "nondual", "Nondual",
        "Who seeks meaning?",
        "The self/world distinction is illusory; the search dissolves.",
        "Reification of separation.",
        ("Adi Shankara", "Laozi"),
        frozenset({S}),
        "Concerns the dissolution of the seeking self; offers no standard for judging an external act.",
    ),
    Tradition(
        "XX", "civilizational", "Civilizational",
        "What remains after I am gone?",
        "Meaning lies in institutions, traditions, and works that outlast the individual.",
        "Short-termism.",
        ("Arnold Toynbee", "Will Durant"),
        frozenset({S, M}),
        "Legacy confers significance and durability is a structural property; mute on whether the legacy is good.",
    ),
    Tradition(
        "XXI", "stoic", "Stoic",
        "What is within my power?",
        "Meaning is found in aligning the will with reason and nature; virtue suffices.",
        "Bondage to passion and circumstance.",
        ("Epictetus", "Marcus Aurelius", "Seneca"),
        frozenset({S}),
        "Its virtue standard is agent-directed (the actor's assent) and does not judge the external act; behaves as significance-only.",
    ),
    Tradition(
        "XXII", "hedonic", "Hedonic",
        "What makes a life worth living from the inside?",
        "Meaning lies in the quality of lived experience and well-being.",
        "The treadmill of escalating desire.",
        ("Epicurus", "Jeremy Bentham"),
        frozenset({S, W}),
        "Felt experience locates significance; welfare is a genuine (if thin) standard for judging acts.",
    ),
    Tradition(
        "XXIII", "theistic", "Theistic",
        "What am I made for?",
        "Meaning derives from a purpose given by God.",
        "Estrangement from the divine.",
        ("Augustine", "Blaise Pascal", "Soren Kierkegaard"),
        frozenset({S, W}),
        "A divine telos both locates significance and supplies a standard for judging acts.",
    ),
    Tradition(
        "XXIV", "nihilist", "Nihilist",
        "What remains once the demand for meaning goes unanswered?",
        "There is no inherent meaning to be found.",
        "Despair, or the manufacture of false comfort.",
        ("Arthur Schopenhauer", "E. M. Cioran", "Albert Camus"),
        frozenset(),
        "The null position: denies a locus of significance and a standard of the good alike. Empty function set by design.",
    ),
    Tradition(
        "XXV", "vocational", "Vocational",
        "Is the work mine, and does it make something worth making?",
        "Meaning is realised through productive work and craft.",
        "Alienation and drudgery.",
        ("Karl Marx", "William Morris", "Matthew Crawford"),
        frozenset({S, W}),
        "Craft locates significance; 'worth making' is a standard by which the made thing is judged.",
    ),
    Tradition(
        "XXVI", "emancipatory", "Emancipatory",
        "Whose freedom does my life serve?",
        "Meaning is found in the struggle for justice and collective liberation.",
        "Complicity, or a cause curdling into domination.",
        ("Frantz Fanon", "Paulo Freire"),
        frozenset({S, W}),
        "Liberation locates significance; justice is a standard for judging whether an act frees or dominates.",
    ),
    Tradition(
        "XXVII", "erotic", "Erotic",
        "Whom do I love, and what does that love open?",
        "Meaning is found in love and the union it seeks.",
        "Possession, or idolatry of the beloved.",
        ("Plato", "Dante"),
        frozenset({S}),
        "Love confers significance; love-as-standard is too contested to count as act-warrant here.",
    ),
)

BY_KEY = {t.key: t for t in LENSBOOK}
ALL_KEYS = tuple(t.key for t in LENSBOOK)


def get(key: str) -> Tradition:
    return BY_KEY[key]
