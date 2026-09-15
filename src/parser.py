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

    def parse(self, text):
        tokens = tokenize(text) if isinstance(text, str) else text
        tokens = [t.lower() for t in tokens]
        if not tokens:
            return ParsedSentence(tokens=tokens)
        if tokens[0] == "what":
            return self.parse_what(tokens)
        if tokens[0] == "who":
            return self.parse_who(tokens)
        return self.parse_statement(tokens)

    def parse_statement(self, tokens):
        # Copular state: Dom is hungry / Dom is sleeping.
        if len(tokens) == 3 and tokens[1] == "is":
            return ParsedSentence(
                subject_word=tokens[0], verb_word=tokens[2],
                rule="state", meaning="SUBJECT_STATE", tokens=tokens
            )

        # Determiner + noun + copula + state: A cat is sleeping.
        if len(tokens) >= 4 and tokens[0] in ("a", "an", "the") and tokens[2] == "is":
            if tokens[3] in ("sleeping", "hungry", "tired", "running"):
                return ParsedSentence(
                    subject_word=tokens[1], verb_word=tokens[3],
                    rule="simple_present_progressive" if tokens[3] == "sleeping" else "state",
                    meaning="SUBJECT_STATE", tokens=tokens
                )

        # Explicit classification: Tom is my cat / Tom is a cat.
        if len(tokens) >= 3 and tokens[1] == "is":
            object_word = tokens[-1]
            if object_word in ("cat", "dog", "mouse", "animal", "mammal"):
                return ParsedSentence(
                    subject_word=tokens[0], verb_word="instance_of", object_word=object_word,
                    rule="instance_of", meaning="TYPE_ASSIGNMENT", tokens=tokens
                )

        # Entity-to-entity relation: Tom is Dom.
        if len(tokens) == 3 and tokens[1] == "is":
            return ParsedSentence(
                subject_word=tokens[0], verb_word="is", object_word=tokens[2],
                rule="entity_relation", meaning="SUBJECT_RELATION", tokens=tokens
            )

        # The cat eats the mouse / Tom eats mouse.
        if len(tokens) >= 3:
            subject = tokens[1] if tokens[0] in ("a", "an", "the") else tokens[0]
            index = 2 if tokens[0] in ("a", "an", "the") else 1
            negated = False
            if index < len(tokens) and tokens[index] == "does":
                index += 1
                if index < len(tokens) and tokens[index] == "not":
                    negated = True
                    index += 1
            if index < len(tokens):
                verb = tokens[index]
                object_index = index + 2 if index + 1 < len(tokens) and tokens[index + 1] in ("a", "an", "the") else index + 1
                if object_index < len(tokens):
                    return ParsedSentence(
                        subject_word=subject, verb_word=verb, object_word=tokens[object_index],
                        negated=negated, rule="simple_present", meaning="SUBJECT_VERB_OBJECT", tokens=tokens
                    )

        return ParsedSentence(tokens=tokens)

    def parse_what(self, tokens):
        # What is Dom? / What is Dom's type?
        if len(tokens) >= 3 and tokens[1] == "is":
            return ParsedSentence(
                subject_word=tokens[2], question_type="TYPE",
                rule="question_what_type", meaning="QUERY_TYPE", tokens=tokens
            )
        if len(tokens) >= 5 and tokens[1] == "does":
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
