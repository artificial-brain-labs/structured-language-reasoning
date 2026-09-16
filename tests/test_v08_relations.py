from src.main import SLR


def test_explicit_eats_relation_is_stored_in_user_memory():
    slr = SLR()
    slr.process("Tom is a cat.")
    slr.process("Tom eats the mouse.")

    tom = slr.user_memory.find_named_entity("Tom")
    mouse = slr.user_memory.find_entity("MOUSE")

    assert tom is not None
    assert mouse is not None
    assert any(
        memory.subject == slr.user_memory.canonical_entity(tom)
        and memory.predicate == "EATS"
        and memory.object == mouse
        and memory.status == "ASSERTED"
        for memory in slr.user_memory.memories
    )


def test_what_does_query_returns_explicit_object_relation():
    slr = SLR()
    slr.process("Tom is a cat.")
    slr.process("Tom eats the mouse.")

    answer = slr.process("What does Tom eat?")

    assert "mouse" in answer.lower()


def test_who_query_returns_explicit_relation_subject():
    slr = SLR()
    slr.process("Tom is a cat.")
    slr.process("Tom eats the mouse.")

    answer = slr.process("Who eats the mouse?")

    assert "tom" in answer.lower()


def test_eats_relation_is_not_invented_by_cat_classification():
    slr = SLR()
    slr.process("Tom is a cat.")

    parsed = slr.parser.parse("What does Tom eat?")
    result = slr.query.answer(parsed)

    assert result == []
    assert not any(
        memory.predicate == "EATS"
        for memory in slr.user_memory.memories
    )


def test_derived_animal_type_does_not_create_derived_eats_fact():
    slr = SLR()
    slr.process("Tom is a cat.")
    slr.process("Tom eats the mouse.")

    tom = slr.user_memory.find_named_entity("Tom")
    mouse = slr.user_memory.find_entity("MOUSE")

    eats = [
        memory
        for memory in slr.user_memory.memories
        if memory.subject == slr.user_memory.canonical_entity(tom)
        and memory.predicate == "EATS"
        and memory.object == mouse
    ]

    assert len(eats) == 1
    assert eats[0].status == "ASSERTED"


def test_unknown_relation_object_does_not_guess_entity_type():
    slr = SLR()
    slr.process("Tom is a cat.")

    response = slr.process("Tom eats the bird.")

    assert response is not None
    bird = slr.user_memory.find_named_entity("bird")
    assert bird is not None
    assert slr.user_memory.entities[bird]["concept"] == "UNKNOWN"


def test_explicit_relation_preserves_no_guessing_for_unknown_subject():
    slr = SLR()

    response = slr.process("Alex eats the mouse.")

    assert "Who is Alex?" in response
    alex = slr.user_memory.find_named_entity("Alex")
    assert alex is not None
    assert slr.user_memory.entities[alex]["concept"] == "UNKNOWN"
