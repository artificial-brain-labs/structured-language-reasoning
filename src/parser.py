import json
from dataclasses import dataclass
from .tokenizer import tokenize
from .compositional_parser import CompositionalGrammarParser


@dataclass
class ParsedSentence:
    subject_word: str | None = None
    verb_word: str | None = None
    object_word: str | None = None
    subject_surface_word: str | None = None
    verb_surface_word: str | None = None
    object_surface_word: str | None = None
    negated: bool = False
    question_type: str | None = None
    rule: str | None = None
    meaning: str | None = None
    operation: str | None = None
    relation: str | None = None
    relationship_target: str | None = None
    tokens: list[str] | None = None


class Parser:
    def __init__(self, lexicon=None, grammar_path="knowledge/grammar.json"):
        self.lexicon = lexicon
        with open(grammar_path, "r", encoding="utf-8") as f:
            self.grammar = json.load(f)
        self.compositional = (
            CompositionalGrammarParser(lexicon)
            if lexicon is not None
            else None
        )

    def _pos(self, word):
        return self.lexicon.pos(word) if self.lexicon else None

    def _concept(self, word):
        if self.lexicon is None:
            return None
        return self.lexicon.concept(word)

    def _category(self, word):
        pos = self._pos(word)
        if pos:
            return pos
        return "ENTITY"

    def _matches_category(self, word, actual, expected):
        if actual == expected:
            return True
        return self._concept(word) == expected

    def _matches(self, tokens, pattern):
        if len(tokens) != len(pattern):
            return False
        return all(
            self._matches_category(token, self._category(token), expected)
            for token, expected in zip(tokens, pattern)
        )

    def _grammar_rule(self, tokens):
        for rule in self.grammar.get("rules", []):
            if self._matches(tokens, rule.get("pattern", [])):
                return rule
        return None

    def _slot_word(self, tokens, rule, slot):
        index = rule.get("slots", {}).get(slot)
        if not isinstance(index, int) or not 0 <= index < len(tokens):
            return None
        return tokens[index]

    def _surface_slot_word(self, surface_tokens, rule, slot):
        index = rule.get("slots", {}).get(slot)
        if not isinstance(index, int) or not 0 <= index < len(surface_tokens):
            return None
        return surface_tokens[index]

    def _from_compositional(self, tokens, surface_tokens):
        if self.compositional is None:
            return None
        start_symbol = "QUESTION" if self._category(tokens[0]) == "QUESTION" else "STATEMENT"
        candidates = self.compositional.parse(tokens, start_symbol=start_symbol)
        if len(candidates) != 1:
            return None
        node = candidates[0]
        production = self.compositional.production_for(node)
        if not production:
            return None

        def token_for(role):
            index = self.compositional.role_token_index(node, role)
            return tokens[index] if index is not None else None

        def surface_for(role):
            index = self.compositional.role_token_index(node, role)
            return surface_tokens[index] if index is not None else None

        return ParsedSentence(
            subject_word=token_for("subject"),
            verb_word=token_for("verb"),
            object_word=token_for("object"),
            subject_surface_word=surface_for("subject"),
            verb_surface_word=surface_for("verb"),
            object_surface_word=surface_for("object"),
            question_type=production.get("question_type"),
            rule=production.get("legacy_rule", production.get("name")),
            meaning=production.get("meaning"),
            operation=production.get("operation"),
            relation=production.get("relation"),
            tokens=tokens,
        )

    def parse(self, text):
        surface_tokens = tokenize(text) if isinstance(text, str) else list(text)
        tokens = [token.lower() for token in surface_tokens]
        if not tokens:
            return ParsedSentence(tokens=tokens)
        compositional = self._from_compositional(tokens, surface_tokens)
        if compositional is not None:
            return compositional
        return self.parse_statement(tokens, surface_tokens=surface_tokens)

    def parse_statement(self, tokens, surface_tokens=None):
        rule = self._grammar_rule(tokens)
        if not rule:
            return ParsedSentence(tokens=tokens)

        surface_tokens = surface_tokens if surface_tokens is not None else tokens
        return ParsedSentence(
            subject_word=self._slot_word(tokens, rule, "subject"),
            verb_word=self._slot_word(tokens, rule, "verb"),
            object_word=self._slot_word(tokens, rule, "object"),
            subject_surface_word=self._surface_slot_word(surface_tokens, rule, "subject"),
            verb_surface_word=self._surface_slot_word(surface_tokens, rule, "verb"),
            object_surface_word=self._surface_slot_word(surface_tokens, rule, "object"),
            question_type=rule.get("question_type"),
            rule=rule.get("name"),
            meaning=rule.get("meaning"),
            operation=rule.get("operation"),
            relation=rule.get("relation"),
            relationship_target=rule.get("relationship_target"),
            tokens=tokens,
        )
