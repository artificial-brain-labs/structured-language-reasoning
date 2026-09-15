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

    def _feature(self, word, name):
        return self.lexicon.feature(word, name) if self.lexicon else None

    def _category(self, word):
        return self._pos(word) or "ENTITY"

    def _matches(self, tokens, pattern):
        if len(tokens) != len(pattern):
            return False
        return all(expected == self._category(token) for token, expected in zip(tokens, pattern))

    def _grammar_rule(self, tokens):
        for rule in self.grammar.get("rules", []):
            if self._matches(tokens, rule["pattern"]):
                return rule
        return None

    def parse(self, text):
        tokens = tokenize(text) if isinstance(text, str) else text
        tokens = [t.lower() for t in tokens]
        if not tokens:
            return ParsedSentence(tokens=tokens)
        if self._is_concept(tokens[0], "WHAT"):
            return self.parse_what(tokens)
        if self._is_concept(tokens[0], "WHO"):
            return self.parse_who(tokens)
        return self.parse_statement(tokens)

    def _is_concept(self, word, concept):
        return self._concept(word) == concept

    def _is_pos(self, word, pos):
        return self._pos(word) == pos

    def parse_statement(self, tokens):
        rule = self._grammar_rule(tokens)
        if rule:
            meaning = rule["meaning"]
            name = rule["name"]

            if meaning == "SUBJECT_STATE":
                if self._is_pos(tokens[0], "DETERMINER"):
                    subject = tokens[1]
                    state = tokens[3]
                else:
                    subject = tokens[0]
                    state = tokens[2]
                return ParsedSentence(
                    subject_word=subject,
                    verb_word=state,
                    rule=name,
                    meaning=meaning,
                    tokens=tokens,
                )

            if meaning == "TYPE_ASSIGNMENT":
                return ParsedSentence(
                    subject_word=tokens[0],
                    verb_word="instance_of",
                    object_word=tokens[-1],
                    rule=name,
                    meaning=meaning,
                    tokens=tokens,
                )

            if meaning == "SUBJECT_RELATION":
                return ParsedSentence(
                    subject_word=tokens[0],
                    verb_word="is",
                    object_word=tokens[2],
                    rule=name,
                    meaning=meaning,
                    tokens=tokens,
                )

            if meaning == "SUBJECT_VERB_OBJECT":
                if self._is_pos(tokens[0], "DETERMINER"):
                    subject = tokens[1]
                    verb_index = 2
                    object_index = 4 if self._is_pos(tokens[3], "DETERMINER") else 3
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
                    tokens=tokens,
                )

        if len(tokens) >= 3 and self._is_concept(tokens[1], "IS"):
            # Preserve the grammar-driven state/type handling for forms whose
            # subject is not lexically classified yet.
            if len(tokens) == 3 and self._is_pos(tokens[2], "STATE"):
                return ParsedSentence(
                    subject_word=tokens[0], verb_word=tokens[2],
                    rule="state", meaning="SUBJECT_STATE", tokens=tokens
                )

        return ParsedSentence(tokens=tokens)

    def parse_what(self, tokens):
        if len(tokens) >= 3 and self._is_concept(tokens[1], "IS"):
            return ParsedSentence(
                subject_word=tokens[2], question_type="TYPE",
                rule="question_what_type", meaning="QUERY_TYPE", tokens=tokens
            )
        if len(tokens) >= 5 and self._is_concept(tokens[1], "DO"):
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
