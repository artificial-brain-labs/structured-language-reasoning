from src.main import SLR


def test_object_query():
    slr = SLR()
    slr.process("The cat eats the mouse.")
    answer = slr.process("What does the cat eat?")
    assert "mouse" in answer.lower()


def test_subject_query():
    slr = SLR()
    slr.process("The cat eats the mouse.")
    answer = slr.process("Who eats the mouse?")
    assert "cat" in answer.lower()


def test_concept_classification_query():
    slr = SLR()
    answer = slr.process("Is a cat an animal?")
    assert answer.lower().startswith("yes")


def test_concept_type_query():
    slr = SLR()
    answer = slr.process("What is a cat?")
    assert "feline" in answer.lower()


def test_malformed_query_is_not_guessed():
    slr = SLR()
    answer = slr.process("Is Tom is mammal?")
    assert "could not parse" in answer.lower()

def test_object_query_with_entity_subject():
    slr = SLR()
    parsed = slr.parser.parse("What Tom eats")

    assert parsed.parse_status == "DETERMINED"
    assert parsed.question_type == "OBJECT"
    assert parsed.subject_word == "tom"
    assert parsed.verb_word == "eats"


def test_object_query_follows_identity_alias():
    slr = SLR()
    slr.process("Tom is a cat.")
    slr.process("Tom eats rat.")
    slr.process("Dom is Tom.")

    answer = slr.process("What Dom eats")
    assert answer == "The Dom eats the rat."



def test_object_query_inherits_relation_from_explicit_classification():
    slr = SLR()
    slr.process("Tom is a cat.")
    slr.process("The cat eats the rat.")

    answer = slr.process("What Tom eats")
    assert answer == "The Tom eats the rat."


def test_subject_query_inherits_relation_from_explicit_classification():
    slr = SLR()
    slr.process("Tom is a cat.")
    slr.process("The cat eats the rat.")

    answer = slr.process("Who eats the rat")
    assert "cat" in answer.lower()
