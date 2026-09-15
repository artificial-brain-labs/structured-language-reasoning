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

    def _concept(self, word):
        return self.lexicon.concept(word) if self.lexicon else None

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

    def parse(self, text):
        tokens = tokenize(text) if isinstance(text, str) else text
        tokens = [token.lower() for token in tokens]
        if not tokens:
            return ParsedSentence(tokens=tokens)
        if self._concept(tokens[0]) == "WHAT":
            return self.parse_what(tokens)
        if self._concept(tokens[0]) == "WHO":
            return self.parse_who(tokens)
        return self.parse_statement(tokens)

    def parse_statement(self, tokens):
        rule = self._grammar_rule(tokens)
        if not rule:
            return ParsedSentence(tokens=tokens)

        meaning = rule.get("meaning")
        operation = rule.get("operation")
        relation = rule.get("relation")
        name = rule.get("name")

        if meaning == "SUBJECT_STATE":
            determiner = self._pos(tokens[0]) == "DETERMINER"
            subject_index = 1 if determiner else 0
            state_index = 3 if determiner else 2
            return ParsedSentence(
                subject_word=tokens[subject_index],
                verb_word=tokens[state_index],
                rule=name,
                meaning=meaning,
                operation=operation,
                relation=relation,
                tokens=tokens,
            )

        if meaning == "TYPE_ASSIGNMENT":
            return ParsedSentence(
                subject_word=tokens[0],
                object_word=tokens[-1],
                rule=name,
                meaning=meaning,
                operation=operation,
                relation=relation,
                tokens=tokens,
            )

        if meaning == "SUBJECT_RELATION":
            return ParsedSentence(
                subject_word=tokens[0],
                object_word=tokens[2],
                rule=name,
                meaning=meaning,
                operation=operation,
                relation=relation,
                tokens=tokens,
            )

        if meaning == "SUBJECT_VERB_OBJECT":
            if self._pos(tokens[0]) == "DETERMINER":
                subject = tokens[1]
                verb_index = 2
                object_index = 4 if self._pos(tokens[3]) == "DETERMINER" else 3
            else:
                subject = tokens[0]
                verb_index = 1
                object_index = 2
            return ParsedSentence(
                subject_word=subject,
                verb_word=tokens[verb_index],
                object_word=tokens[object_index],
                rule=name,
                meaning=meaning,
                operation=operation,
                relation=relation,
                tokens=tokens,
            )

        return ParsedSentence(tokens=tokens)

    def parse_what(self, tokens):
        if len(tokens) >= 3 and self._concept(tokens[1]) == "IS":
            return ParsedSentence(
                subject_word=tokens[2], question_type="TYPE",
                rule="question_what_type", meaning="QUERY_TYPE", tokens=tokens
            )
        if len(tokens) >= 5 and self._concept(tokens[1]) == "DO":
            return ParsedSentence(
                subject_word=tokens[3], verb_word=tokens[4], question_type="OBJECT",
                rule="question_what_object", meaning="QUERY_OBJECT", tokens=tokens
            )
        return ParsedSentence(tokens=tokens)

    def parse_who(self, tokens):
        if len(tokens) >= 4:
            return ParsedSentence(
                verb_word=tokens[1], object_word=tokens[3], question_type="SUBJECT",
                rule="question_who_subject", meaning="QUERY_SUBJECT", tokens=tokens
            )
        return ParsedSentence(tokens=tokens)
