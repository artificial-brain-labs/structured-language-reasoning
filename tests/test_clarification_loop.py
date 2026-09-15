from src.main import SLR


def test_unknown_name_triggers_clarification_then_type_update():
    slr = SLR()

    first = slr.process("Tom is sleeping.")
    assert "Who is Tom?" in first
    tom = slr.memory.find_named_entity("Tom")
    assert tom is not None
    assert slr.memory.entities[tom]["concept"] == "UNKNOWN"
    assert any(m.subject == tom and m.predicate == "SLEEPING" for m in slr.memory.memories)

    second = slr.process("Tom is my cat.")
    assert "is a cat" in second
    assert slr.memory.entities[tom]["concept"] == "CAT"
    assert slr.ontology.is_a("CAT", "LIVING_THING")


def test_unknown_remains_unknown_without_guessing():
    slr = SLR()
    slr.process("Alex is sleeping.")
    alex = slr.memory.find_named_entity("Alex")
    assert slr.memory.entities[alex]["concept"] == "UNKNOWN"
