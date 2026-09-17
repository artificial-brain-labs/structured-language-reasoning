from dataclasses import dataclass, field
import re


@dataclass(frozen=True)
class SemanticContext:
    """Structured, parser-derived context for a communication."""
    text: str
    subject: str | None = None
    predicate: str | None = None
    object: str | None = None
    concepts: tuple[str, ...] = ()
    tokens: tuple[str, ...] = ()
    features: dict = field(default_factory=dict)


class SemanticContextExtractor:
    """Extract context from the existing structured parser/semantic layers.

    This component does not infer unstated facts. It only projects information
    already present in the parsed sentence and dictionary.
    """

    def __init__(self, lexicon=None):
        self.lexicon = lexicon

    def _concept(self, word):
        if not word or self.lexicon is None:
            return None
        senses = self.lexicon.senses(word) if hasattr(self.lexicon, "senses") else []
        if len(senses) == 1:
            return senses[0].concept
        return None

    def extract(self, parsed, text=None):
        tokens = tuple(parsed.tokens or ())
        concepts = []
        for token in tokens:
            concept = self._concept(token)
            if concept and concept not in concepts:
                concepts.append(concept)

        features = {}
        if parsed.question_type:
            features["question_type"] = parsed.question_type
        if parsed.rule:
            features["grammar_rule"] = parsed.rule
        if parsed.operation:
            features["operation"] = parsed.operation
        if parsed.relation:
            features["relation"] = parsed.relation

        return SemanticContext(
            text=text or " ".join(tokens),
            subject=parsed.subject_word,
            predicate=parsed.verb_word,
            object=parsed.object_word,
            concepts=tuple(concepts),
            tokens=tokens,
            features=features,
        )
