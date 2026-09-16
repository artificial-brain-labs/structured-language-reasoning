import json
from dataclasses import dataclass
from .tokenizer import tokenize


@dataclass
class ParsedSentence:
    subject_word: str | None = None
    verb_word: str | None = None
    object_word: str | None = None
    negated: bool = False
    question_type: str | None = None
    rule: str | None = None
    meaning: str | None = None
    operation: str | None = None
    relation: str | None = None
    tokens: list[str] | None = None


class Parser:
    def __init__(self, lexicon=None, grammar_path="knowledge/grammar.json"):
        self.lexicon = lexicon
        with open(grammar_path, "r", encoding="utf-8") as f:
            self.grammar = json.load(f)

    def _pos(self, word):
        return self.lexicon.pos(word) if self.lexicon else None

    def _category(self, word):
        """Resolve a token to the category used by the declarative grammar.

        ENTITY is a syntactic placeholder for an unresolved named entity.
        It does not assert the entity's real-world type.
        """
        pos = self._pos(word)
        if pos:
            return pos
        return "ENTITY"

    def _matches_category(self, actual, expected):
        # ENTITY is an unresolved entity candidate. It is intentionally
        # distinct from lexical NOUN so grammar rules can require either a
        # known lexical noun or an unresolved name.
        return actual == expected

    def _matches(self, tokens, pattern):
        if len(tokens) != len(pattern):
            return False
        return all(
            self._matches_category(self._category(token), expected)
            for token, expected in zip(tokens, pattern)
        )

    def _grammar_rule(self, tokens):
        for rule in self.grammar.get("rules", []):
            if self._matches(tokens, rule.get("pattern", [])):
                return rule
        return None

    def _slot_word(self, tokens, rule, slot):
        """Read a semantic slot from declarative grammar data."""
        index = rule.get("slots", {}).get(slot)
        if not isinstance(index, int) or not 0 <= index < len(tokens):
            return None
        return tokens[index]

    def parse(self, text):
        surface_tokens = tokenize(text) if isinstance(text, str) else list(text)
        tokens = [token.lower() for token in surface_tokens]
        if not tokens:
            return ParsedSentence(tokens=tokens)
        return self.parse_statement(tokens, surface_tokens=surface_tokens)

    def parse_statement(self, tokens, surface_tokens=None):
        rule = self._grammar_rule(tokens)
        if not rule:
            return ParsedSentence(tokens=tokens)

        surface_tokens = surface_tokens if surface_tokens is not None else tokens
        return ParsedSentence(
            subject_word=self._slot_word(surface_tokens, rule, "subject"),
            verb_word=self._slot_word(surface_tokens, rule, "verb"),
            object_word=self._slot_word(surface_tokens, rule, "object"),
            question_type=rule.get("question_type"),
            rule=rule.get("name"),
            meaning=rule.get("meaning"),
            operation=rule.get("operation"),
            relation=rule.get("relation"),
            tokens=tokens,
        )
