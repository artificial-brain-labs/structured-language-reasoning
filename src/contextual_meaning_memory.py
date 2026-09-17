from dataclasses import dataclass, field
from datetime import datetime, UTC


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
    """Persistent contextual meaning memory.

    It never changes the dictionary. It records explicit user resolutions so
    future language understanding can reuse them as evidence.
    """

    def __init__(self):
        self.resolutions = []

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

    def preferred_sense(self, word, context):
        matches = self.find(word, context)
        if not matches:
            return None
        return matches[-1].selected_sense_id

    def clear(self):
        self.resolutions.clear()
