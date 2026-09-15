from src.lexicon import Lexicon
from src.parser import Parser


def test_statement_slots_are_read_from_grammar():
    parser = Parser(Lexicon())

    state = parser.parse("A cat is sleeping.")
    assert (state.subject_word, state.verb_word) == ("cat", "sleeping")

    transitive = parser.parse("The cat eats the mouse.")
    assert (transitive.subject_word, transitive.verb_word, transitive.object_word) == (
        "cat", "eats", "mouse"
    )

    unknown_subject = parser.parse("Tom eats mouse.")
    assert (unknown_subject.subject_word, unknown_subject.verb_word, unknown_subject.object_word) == (
        "tom", "eats", "mouse"
    )

    classification = parser.parse("Tom is a cat.")
    assert (classification.subject_word, classification.object_word) == ("tom", "cat")

    identity = parser.parse("Tom is Dom.")
    assert (identity.subject_word, identity.object_word) == ("tom", "dom")


def test_question_slots_are_read_from_grammar():
    parser = Parser(Lexicon())

    type_question = parser.parse("What is Tom?")
    assert type_question.question_type == "TYPE"
    assert type_question.subject_word == "tom"

    object_question = parser.parse("What does the cat eat?")
    assert object_question.question_type == "OBJECT"
    assert (object_question.subject_word, object_question.verb_word) == ("cat", "eat")

    subject_question = parser.parse("Who eats the mouse?")
    assert subject_question.question_type == "SUBJECT"
    assert (subject_question.verb_word, subject_question.object_word) == ("eats", "mouse")
