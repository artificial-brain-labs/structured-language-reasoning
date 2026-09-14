from dataclasses import dataclass

from .tokenizer import tokenize


@dataclass
class ParsedSentence:
    subject_word: str | None = None
    verb_word: str | None = None
    object_word: str | None = None
    negated: bool = False
    question_type: str | None = None

    # V0.1 compatibility
    rule: str | None = None
    meaning: str | None = None

    # Preserve original linguistic representation
    tokens: list[str] | None = None


class Parser:

    def __init__(self, lexicon=None):
        self.lexicon = lexicon

    def parse(self, text):

        if isinstance(text, str):
            tokens = tokenize(text)
        else:
            tokens = text

        if not tokens:
            return ParsedSentence(tokens=tokens)

        if tokens[0] == "what":
            return self.parse_what(tokens)

        if tokens[0] == "who":
            return self.parse_who(tokens)

        return self.parse_statement(tokens)

    def parse_statement(self, tokens):

        # A cat is sleeping.
        if (
            len(tokens) >= 4
            and tokens[0] in ("a", "an", "the")
            and tokens[2] == "is"
            and tokens[3] == "sleeping"
        ):
            return ParsedSentence(
                subject_word=tokens[1],
                verb_word="sleeping",
                rule="simple_present_progressive",
                meaning="SUBJECT_STATE",
                tokens=tokens
            )

        # The cat eats the mouse.
        if len(tokens) >= 5:

            subject = tokens[1]
            index = 2
            negated = False

            # The cat does not eat the mouse.
            if tokens[index] == "does":

                index += 1

                if (
                    index < len(tokens)
                    and tokens[index] == "not"
                ):
                    negated = True
                    index += 1

                if index >= len(tokens):
                    return ParsedSentence(tokens=tokens)

            verb = tokens[index]
            object_index = index + 2

            if object_index < len(tokens):

                return ParsedSentence(
                    subject_word=subject,
                    verb_word=verb,
                    object_word=tokens[object_index],
                    negated=negated,
                    rule="simple_present",
                    meaning="SUBJECT_VERB_OBJECT",
                    tokens=tokens
                )

        return ParsedSentence(tokens=tokens)

    def parse_what(self, tokens):

        # What does the cat eat?
        if (
            len(tokens) >= 5
            and tokens[1] == "does"
        ):
            return ParsedSentence(
                subject_word=tokens[3],
                verb_word=tokens[4],
                question_type="OBJECT",
                rule="question_what_object",
                meaning="QUERY_OBJECT",
                tokens=tokens
            )

        return ParsedSentence(tokens=tokens)

    def parse_who(self, tokens):

        # Who eats the mouse?
        if len(tokens) >= 4:

            return ParsedSentence(
                verb_word=tokens[1],
                object_word=tokens[3],
                question_type="SUBJECT",
                rule="question_who_subject",
                meaning="QUERY_SUBJECT",
                tokens=tokens
            )

        return ParsedSentence(tokens=tokens)