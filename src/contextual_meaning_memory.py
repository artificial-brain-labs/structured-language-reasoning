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
    semantic_context: object = None
    source: str = "USER_CLARIFICATION"
    status: str = "CONFIRMED"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class ContextualMeaningMemory:
    """Persistent memory of explicit lexical meaning resolutions.

    The memory stores experiences, not dictionary changes. Context matching is
    deterministic and evidence-based; equal competing evidence remains ambiguous.
    """

    STOPWORDS = {
        "a", "an", "the", "is", "am", "are", "was", "were", "be", "to",
        "of", "in", "on", "at", "for", "and", "or", "i", "you", "he",
        "she", "it", "we", "they", "my", "your", "this", "that", "with",
    }

    def __init__(self, lexicon=None):
        if lexicon is None:
            from .lexicon import Lexicon
            lexicon = Lexicon()
        self.lexicon = lexicon
        self.resolutions = []

    def _tokens(self, text):
        return {
            token for token in re.findall(r"[a-z0-9]+", text.lower())
            if token not in self.STOPWORDS
        }

    def _sense_anchors(self, sense_id):
        """Return dictionary-definition words associated with a learned sense."""
        if self.lexicon is None:
            return set()
        for word, entry in self.lexicon.words.items():
            for sense in entry.get("senses", []):
                if sense.get("id") == sense_id:
                    definition = sense.get("definition") or ""
                    return self._tokens(definition)
        return set()

    def _context_signature(self, word, context):
        target = word.lower()
        return self._tokens(context) - {target}

    def _semantic_signature(self, semantic_context):
        if semantic_context is None:
            return set()
        values = set(getattr(semantic_context, "concepts", ()) or ())
        for value in (
            getattr(semantic_context, "predicate", None),
            getattr(semantic_context, "object", None),
            getattr(semantic_context, "subject", None),
        ):
            if value:
                values.add(value.lower())
        return values

    def learn(self, word, selected_sense_id, candidate_sense_ids, context, semantic_context=None):
        resolution = MeaningResolution(
            word=word.lower(),
            selected_sense_id=selected_sense_id,
            candidate_sense_ids=tuple(candidate_sense_ids),
            context=context.strip(),
            semantic_context=semantic_context,
        )
        self.resolutions.append(resolution)
        return resolution

    def find(self, word, context=None):
        word = word.lower()
        matches = [r for r in self.resolutions if r.word == word and r.status == "CONFIRMED"]
        if context is None:
            return matches
        return [r for r in matches if r.context.lower() == context.strip().lower()]

    def match(self, word, context, semantic_context=None):
        """Return equally best learned interpretations with evidence.

        Evidence consists of:
        - direct contextual word overlap;
        - overlap with dictionary-definition anchors for the learned sense.

        A single best result is not sufficient by itself if the evidence is tied
        between different senses.
        """
        current = self._context_signature(word, context)
        current_semantic = self._semantic_signature(semantic_context)
        if not current and not current_semantic:
            return []

        candidates = []
        for resolution in self.find(word):
            learned_context = self._context_signature(word, resolution.context)
            direct = current & learned_context
            semantic = current & self._sense_anchors(resolution.selected_sense_id)
            learned_semantic = self._semantic_signature(resolution.semantic_context)
            semantic_structure = current_semantic & learned_semantic
            score = len(direct) + len(semantic) + len(semantic_structure)
            if score:
                candidates.append({
                    "score": score,
                    "resolution": resolution,
                    "direct_evidence": sorted(direct),
                    "semantic_evidence": sorted(semantic | semantic_structure),
                })

        if not candidates:
            return []
        best_score = max(item["score"] for item in candidates)
        return [item for item in candidates if item["score"] == best_score]

    def preferred_sense(self, word, context, semantic_context=None):
        matches = self.match(word, context, semantic_context=semantic_context)
        if not matches:
            return None
        sense_ids = {item["resolution"].selected_sense_id for item in matches}
        if len(sense_ids) != 1:
            return None
        return next(iter(sense_ids))

    def evidence(self, word, context, semantic_context=None):
        return self.match(word, context, semantic_context=semantic_context)

    def clear(self):
        self.resolutions.clear()
