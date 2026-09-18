from dataclasses import dataclass, field


@dataclass(frozen=True)
class MeaningCandidate:
    """One dictionary-backed interpretation of a lexical item."""
    sense_id: str
    concept: str | None
    pos: str | None
    definition: str | None = None
    evidence: tuple = ()
    semantic_profile: dict = field(default_factory=dict)


@dataclass
class AmbiguityResult:
    """Result of meaning selection without silently guessing."""
    status: str
    candidates: list[MeaningCandidate] = field(default_factory=list)
    selected: MeaningCandidate | None = None
    reason: str | None = None


class AmbiguityResolver:
    """Resolve dictionary senses using explicit constraints only.

    A single candidate is selected only when the supplied constraints leave
    exactly one candidate. Confidence is never converted into truth here.
    """

    def resolve(self, candidates, allowed_pos=None, required_concept=None):
        candidates = list(candidates)
        if allowed_pos:
            candidates = [c for c in candidates if c.pos in set(allowed_pos)]
        if required_concept:
            candidates = [c for c in candidates if c.concept == required_concept]

        if not candidates:
            return AmbiguityResult("UNKNOWN", reason="No dictionary sense satisfies the constraints.")
        if len(candidates) == 1:
            return AmbiguityResult("RESOLVED", candidates=candidates, selected=candidates[0])
        return AmbiguityResult("AMBIGUOUS", candidates=candidates,
                               reason="Multiple dictionary senses remain possible.")
