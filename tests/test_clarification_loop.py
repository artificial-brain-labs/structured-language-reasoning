from src.main import SLR


def test_unknown_name_triggers_clarification_then_user_memory_update():
    slr = SLR()

    first = slr.process("Tom is sleeping.")
    assert "Who is Tom?" in first
    tom = slr.user_memory.find_named_entity("Tom")
    assert tom is not None
    assert slr.user_memory.entities[tom]["concept"] == "UNKNOWN"
    assert any(m.subject == tom and m.predicate == "SLEEP" for m in slr.user_memory.memories)
    assert slr.memory.find_named_entity("Tom") is None

    second = slr.process("Tom is my cat.")
    assert "is a cat" in second
    assert slr.user_memory.entities[tom]["concept"] == "UNKNOWN"
    cat = slr.user_memory.find_entity("CAT")
    assert any(
        m.subject == tom
        and m.predicate == "IS_A"
        and m.object == cat
        and m.status == "ASSERTED"
        for m in slr.user_memory.memories
    )
    assert not any(
        m.subject == tom and m.predicate == "IS_A"
        for m in slr.memory.memories
    )
    assert slr.ontology.is_a("CAT", "LIVING_THING")


def test_unknown_remains_unknown_without_guessing():
    slr = SLR()
    slr.process("Alex is sleeping.")
    alex = slr.user_memory.find_named_entity("Alex")
    assert slr.user_memory.entities[alex]["concept"] == "UNKNOWN"
    assert slr.memory.find_named_entity("Alex") is None
