from src.main import SLR


def test_clarification_resumes_only_after_relation_validation():
    slr = SLR()

    first = slr.process("Tom eats mouse.")
    assert "Who is Tom?" in first

    tom = slr.memory.find_named_entity("Tom")
    mouse = slr.memory.find_entity("MOUSE")
    assert tom is not None
    assert mouse is not None

    second = slr.process("Tom is a chair.")
    assert "could not validate the earlier statement" in second

    tom = slr.memory.find_named_entity("Tom")
    assert slr.memory.entities[tom]["concept"] == "CHAIR"
    assert not any(
        m.subject == tom and m.predicate == "EATS" and m.object == mouse
        for m in slr.memory.memories
    )


def test_clarification_resumes_valid_relation_after_classification():
    slr = SLR()

    first = slr.process("Tom eats mouse.")
    assert "Who is Tom?" in first

    tom = slr.memory.find_named_entity("Tom")
    mouse = slr.memory.find_entity("MOUSE")
    assert tom is not None
    assert mouse is not None

    second = slr.process("Tom is a cat.")
    assert "stored the earlier statement" in second

    tom = slr.memory.find_named_entity("Tom")
    assert slr.memory.entities[tom]["concept"] == "CAT"
    assert any(
        m.subject == tom and m.predicate == "EATS" and m.object == mouse
        for m in slr.memory.memories
    )
