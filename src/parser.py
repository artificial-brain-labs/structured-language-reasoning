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
    def __init__(self, lexicon=None):
        self.lexicon = lexicon

    def _pos(self, word):
        return self.lexicon.pos(word) if self.lexicon else None

    def _concept(self, word):
        return self.lexicon.concept(word) if self.lexicon else None

    def _feature(self, word, name):
        return self.lexicon.feature(word, name) if self.lexicon else None

    def _is_concept(self, word, concept):
        return self._concept(word) == concept

    def _is_pos(self, word, pos):
        return self._pos(word) == pos

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

    def parse_statement(self, tokens):
        if len(tokens) >= 3 and self._is_concept(tokens[1], "IS"):
            subject = tokens[0]
            object_word = tokens[-1]

            if len(tokens) >= 4 and self._is_pos(tokens[0], "DETERMINER"):
                state = tokens[3]
                if self._is_pos(state, "STATE"):
                    rule = "state"
                    if self._feature(state, "aspect"):
                        rule = f"{self._feature(state, 'aspect').lower()}_state"
                    return ParsedSentence(
                        subject_word=tokens[1], verb_word=state,
                        rule=rule, meaning="SUBJECT_STATE", tokens=tokens
                    )

            if len(tokens) == 3 and self._is_pos(object_word, "STATE"):
                return ParsedSentence(
                    subject_word=subject, verb_word=object_word,
                    rule="state", meaning="SUBJECT_STATE", tokens=tokens
                )

            if self._is_pos(object_word, "NOUN"):
                return ParsedSentence(
                    subject_word=subject, verb_word="instance_of", object_word=object_word,
                    rule="instance_of", meaning="TYPE_ASSIGNMENT", tokens=tokens
                )

            if len(tokens) == 3:
                return ParsedSentence(
                    subject_word=subject, verb_word="is", object_word=object_word,
                    rule="entity_relation", meaning="SUBJECT_RELATION", tokens=tokens
                )

        if len(tokens) >= 3:
            offset = 1
            subject = tokens[0]
            if self._is_pos(tokens[0], "DETERMINER") and len(tokens) > 1:
                subject = tokens[1]
                offset = 2

            negated = False
            if offset < len(tokens) and self._is_concept(tokens[offset], "DO"):
                offset += 1
                if offset < len(tokens) and self._is_pos(tokens[offset], "NEGATION"):
                    negated = True
                    offset += 1

            if offset < len(tokens):
                verb = tokens[offset]
                object_index = offset + 1
                if object_index < len(tokens) and self._is_pos(tokens[object_index], "DETERMINER"):
                    object_index += 1
                if object_index < len(tokens):
                    return ParsedSentence(
                        subject_word=subject, verb_word=verb, object_word=tokens[object_index],
                        negated=negated, rule="simple_present", meaning="SUBJECT_VERB_OBJECT", tokens=tokens
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
