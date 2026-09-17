import json
from .ambiguity import AmbiguityResolver, MeaningCandidate


class Lexicon:
    def __init__(self, path="knowledge/lexicon.json"):
        with open(path, "r", encoding="utf-8") as f:
            self.words = json.load(f)

    def get(self, word):
        return self.words.get(word.lower()) if isinstance(word, str) else None

    def concept(self, word):
        entry = self.get(word)
        return entry.get("concept") if entry else None

    def pos(self, word):
        entry = self.get(word)
        return entry.get("pos") if entry else None

    def relation(self, word):
        entry = self.get(word)
        return entry.get("relation") if entry else None

    def feature(self, word, name):
        entry = self.get(word)
        return entry.get(name) if entry else None

    def contains(self, word):
        return isinstance(word, str) and word.lower() in self.words

    def senses(self, word):
        entry = self.get(word)
        if not entry:
            return []
        explicit = entry.get('senses')
        if explicit:
            return [MeaningCandidate(s.get('id', f"{word.lower()}.{i}"), s.get('concept'), s.get('pos'), s.get('definition')) for i, s in enumerate(explicit, 1)]
        return [MeaningCandidate(f"{word.lower()}.default", entry.get('concept'), entry.get('pos'), entry.get('definition'))]

    def meanings(self, word):
        return self.senses(word)

    def resolve_meaning(self, word, allowed_pos=None, required_concept=None):
        resolver = AmbiguityResolver()
        return resolver.resolve(self.senses(word), allowed_pos=allowed_pos, required_concept=required_concept)
