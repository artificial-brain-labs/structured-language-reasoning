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
        return self._pos(word) or "ENTITY"

    def _matches(self, tokens, pattern):
        return len(tokens) == len(pattern) and all(
            expected == self._category(token)
            for token, expected in zip(tokens, pattern)
        )

    def _grammar_rule(self, tokens):
        return next(
            (rule for rule in self.grammar.get("rules", [])
             if self._matches(tokens, rule["pattern"])),
            None,
        )

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
        relation = rule.get("relation")
        name = rule.get("name")

        if meaning == "SUBJECT_STATE":
            if self._pos(tokens[0]) == "DETERMINER":
                subject, state = tokens[1], tokens[3]
            else:
                subject, state = tokens[0], tokens[2]
            return ParsedSentence(
                subject_word=subject,
                verb_word=state,
                rule=name,
                meaning=meaning,
                relation=relation,
                tokens=tokens,
            )

        if meaning == "TYPE_ASSIGNMENT":
            return ParsedSentence(
                subject_word=tokens[0],
                object_word=tokens[-1],
                rule=name,
                meaning=meaning,
                relation=relation,
                tokens=tokens,
            )

        if meaning == "SUBJECT_RELATION":
            return ParsedSentence(
                subject_word=tokens[0],
                object_word=tokens[2],
                rule=name,
                meaning=meaning,
                relation=relation,
                tokens=tokens,
            )

        if meaning == "SUBJECT_VERB_OBJECT":
            if self._pos(tokens[0]) == "DETERMINER":
                subject = tokens[1]
                verb_index = 2
                object_index = 4 if self._pos(tokens[3]) == "DETERMINER" else 3
            else:
                subject, verb_index, object_index = tokens[0], 1, 2
            return ParsedSentence(
                subject_word=subject,
                verb_word=tokens[verb_index],
                object_word=tokens[object_index],
                rule=name,
                meaning=meaning,
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
