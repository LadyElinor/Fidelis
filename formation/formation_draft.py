"""Formation-hazard lens.

Most of what TrustedRuntime judges is an *act with a target* -- a code change, a
release, an operation. A distinct and easily-missed class of act has no single
target and instead *forms a population's priors at scale*: publishing a training
corpus, shipping a recommender, seeding a curriculum, releasing generated media.
These are formation/canonization events, and the governing fact about them is
that they install beliefs without arguing for them -- so they bypass exactly the
deliberative scrutiny the rest of the stack assumes an act will receive.

This lens does not deliver a warrant verdict (that is the warrant layer's job).
It is a *hazard* detector in the council's sense: it raises fault lines a human
reviewer should see before a formation event proceeds. The hazards it names are
the ones formation research identifies as load-bearing:

- scale without consent  : priors installed across a population that never argued back
- canonization power      : the act also selects which content others encounter
                            (a corpus, syllabus, ranking) -- an institutional filter
- amplified under depletion: formation bites hardest under stress/isolation/repetition,
                            which is the audience state mass media often finds
- no correction loop      : the act offers no adversarial contact with the territory
                            that could falsify what it installs
- replication-blind canon : famous claims propagated without their replication status

The lens is deliberately conservative: it fires only on actions that declare or
plainly describe a formation/canonization purpose, and every hazard it raises is
contestable data, attributed to this lens, never a silent override.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Context keys an action may set to declare formation scope explicitly.
# Declared intent is authoritative; the keyword scan below is only a fallback.
FORMATION_KINDS = frozenset({
    "training_corpus", "model_training_data", "curriculum", "recommender",
    "ranking_change", "generated_media_release", "canon_selection",
    "syllabus", "content_amplification",
})

CANONIZATION_KINDS = frozenset({
    "training_corpus", "model_training_data", "curriculum", "syllabus",
    "ranking_change", "recommender", "canon_selection", "content_amplification",
})

# Fallback signal only. Phrases that plainly describe forming priors at scale.
_FORMATION_PHRASES = (
    "training corpus", "training data", "fine-tune", "fine tune", "pretraining",
    "curriculum", "syllabus", "recommendation algorithm", "recommender",
    "ranking model", "feed ranking", "canon", "reading list", "at population scale",
    "shape behavior", "shape behaviour", "influence beliefs", "form priors",
)


@dataclass(frozen=True)
class FormationHazardReport:
    is_formation_event: bool
    is_canonization_event: bool
    hazards: tuple[str, ...] = ()
    fault_lines: tuple[str, ...] = ()
    rationale: str = ""
    # explicit so a downstream receipt can record what the lens keyed on
    matched_kind: str | None = None
    matched_phrase: str | None = None


def _classify(description: str, context: dict) -> tuple[bool, bool, str | None, str | None]:
    declared = context.get("change_type") or context.get("action_kind")
    if declared in FORMATION_KINDS:
        return True, declared in CANONIZATION_KINDS, declared, None
    text = (description or "").lower()
    for phrase in _FORMATION_PHRASES:
        if phrase in text:
            # canonization if the matched phrase is a selection mechanism
            canon = phrase in (
                "training corpus", "training data", "fine-tune", "fine tune",
                "pretraining", "curriculum", "syllabus", "recommendation algorithm",
                "recommender", "ranking model", "feed ranking", "canon", "reading list",
            )
            return True, canon, None, phrase
    return False, False, None, None


def assess_formation_hazard(description: str, context: dict | None = None) -> FormationHazardReport:
    """Raise formation/canonization hazards for a proposed action. Additive: returns
    an empty (non-firing) report for the ordinary case so callers can always merge it."""
    context = context or {}
    is_formation, is_canon, kind, phrase = _classify(description, context)
    if not is_formation:
        return FormationHazardReport(False, False, rationale="no formation/canonization scope detected")

    hazards: list[str] = ["formation::scale_without_consent"]
    fault_lines: list[str] = [
        "priors installed across an audience that does not argue back"
    ]

    if is_canon:
        hazards.append("formation::canonization_power")
        fault_lines.append(
            "the act selects which content others encounter; canonization is an "
            "institutional filter, not a meritocratic one"
        )
        # the module's own audit requirement, surfaced as a hazard
        hazards.append("formation::replication_blind_canon")
        fault_lines.append(
            "famous claims may propagate without their replication status attached"
        )

    # depletion amplification and the missing correction loop apply to any
    # formation event; they are the two findings that make formation dangerous
    # rather than merely present.
    hazards.append("formation::amplified_under_depletion")
    hazards.append("formation::no_correction_loop")
    fault_lines.append(
        "no adversarial contact with the territory is provided that could "
        "falsify what the act installs"
    )

    declared = kind is not None
    rationale = (
        f"formation event detected via {'declared change_type' if declared else 'description scan'}"
        f" ({kind or phrase}); "
        f"{'also a canonization event' if is_canon else 'not a canonization event'}. "
        "Effects are typically small but cumulative; hazard is the absence of scrutiny "
        "an argued claim would receive, not the content itself."
    )
    return FormationHazardReport(
        is_formation_event=True,
        is_canonization_event=is_canon,
        hazards=tuple(hazards),
        fault_lines=tuple(fault_lines),
        rationale=rationale,
        matched_kind=kind,
        matched_phrase=phrase,
    )
