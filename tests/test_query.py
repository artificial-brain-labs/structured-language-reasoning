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
