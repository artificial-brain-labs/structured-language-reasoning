from src.main import SLR


def test_clarification_resumes_only_after_relation_validation():
    slr = SLR()

    first = slr.process("Tom eats mouse.")
    assert "Who is Tom?" in first

    tom = slr.user_memory.find_named_entity("Tom")
    mouse = slr.user_memory.find_entity("MOUSE")
    assert tom is not None
    assert mouse is not None

    second = slr.process("Tom is a chair.")
    assert "could not validate the earlier statement" in second

    tom = slr.user_memory.find_named_entity("Tom")
    assert slr.user_memory.entities[tom]["concept"] == "UNKNOWN"
    assert any(
        m.subject == tom
        and m.predicate == "IS_A"
        and m.object == slr.user_memory.find_entity("CHAIR")
        and m.status == "ASSERTED"
        for m in slr.user_memory.memories
    )
    assert not any(
        m.subject == tom and m.predicate == "EATS" and m.object == mouse
        for m in slr.user_memory.memories
    )


def test_clarification_resumes_valid_relation_after_classification():
    slr = SLR()

    first = slr.process("Tom eats mouse.")
    assert "Who is Tom?" in first

    tom = slr.user_memory.find_named_entity("Tom")
    mouse = slr.user_memory.find_entity("MOUSE")
    assert tom is not None
    assert mouse is not None

    second = slr.process("Tom is a cat.")
    assert "stored the earlier statement" in second

    tom = slr.user_memory.find_named_entity("Tom")
    assert slr.user_memory.entities[tom]["concept"] == "UNKNOWN"
    assert any(
        m.subject == tom
        and m.predicate == "IS_A"
        and m.object == slr.user_memory.find_entity("CAT")
        and m.status == "ASSERTED"
        for m in slr.user_memory.memories
    )
    assert any(
        m.subject == tom and m.predicate == "EATS" and m.object == mouse
        for m in slr.user_memory.memories
    )
