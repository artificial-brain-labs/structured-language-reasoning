from dataclasses import dataclass, field
from datetime import datetime, UTC
import re


@dataclass
class MeaningResolution:
    """A user-confirmed contextual interpretation of a lexical ambiguity."""
    word: str
    selected_sense_id: str
    candidate_sense_ids: tuple[str, ...]
    context: str
    source: str = "USER_CLARIFICATION"
    status: str = "CONFIRMED"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class ContextualMeaningMemory:
    """Persistent memory of explicit lexical ambiguity resolutions.

    CMM never changes dictionary meanings. It stores user-confirmed resolutions
    and can reuse them only when explicit contextual evidence matches.
    """

    STOPWORDS = {
        "a", "an", "the", "is", "am", "are", "was", "were", "be", "to",
        "of", "in", "on", "at", "for", "and", "or", "i", "you", "he",
        "she", "it", "we", "they", "my", "your", "this", "that",
    }

    def __init__(self):
        self.resolutions = []

    def _tokens(self, text):
        return [
            token for token in re.findall(r"[a-z0-9]+", text.lower())
            if token not in self.STOPWORDS
        ]

    def _context_signature(self, word, context):
        target = word.lower()
        return tuple(token for token in self._tokens(context) if token != target)

    def learn(self, word, selected_sense_id, candidate_sense_ids, context):
        resolution = MeaningResolution(
            word=word.lower(),
            selected_sense_id=selected_sense_id,
            candidate_sense_ids=tuple(candidate_sense_ids),
            context=context.strip(),
        )
        self.resolutions.append(resolution)
        return resolution

    def find(self, word, context=None):
        word = word.lower()
        matches = [r for r in self.resolutions if r.word == word and r.status == "CONFIRMED"]
        if context is None:
            return matches
        return [r for r in matches if r.context.lower() == context.strip().lower()]

    def match(self, word, context):
        """Return learned matches ranked by explicit lexical context overlap.

        A match requires at least one shared non-stopword context token.
        Ties are returned as ambiguous rather than guessed away.
        """
        candidates = []
        current = set(self._context_signature(word, context))
        if not current:
            return []
        for resolution in self.find(word):
            learned = set(self._context_signature(word, resolution.context))
            overlap = current & learned
            if overlap:
                candidates.append((len(overlap), resolution, overlap))
        candidates.sort(key=lambda item: item[0], reverse=True)
        if not candidates:
            return []
        best_score = candidates[0][0]
        return [item for item in candidates if item[0] == best_score]

    def preferred_sense(self, word, context):
        matches = self.match(word, context)
        if not matches:
            return None
        sense_ids = {item[1].selected_sense_id for item in matches}
        if len(sense_ids) != 1:
            return None
        return next(iter(sense_ids))

    def clear(self):
        self.resolutions.clear()
