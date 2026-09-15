from src.main import SLR


def test_unknown_state_preserves_no_guessing_and_clarifies():
    slr = SLR()

    response = slr.process("Tom is sleeping.")

    assert "Who is Tom?" in response
    tom = slr.memory.find_named_entity("Tom")
    assert tom is not None
    assert slr.memory.entities[tom]["concept"] == "UNKNOWN"


def test_classification_and_identity_execute_through_operation_layer():
    slr = SLR()

    slr.process("Dom is my cat.")
    slr.process("Tom is Dom.")

    tom = slr.memory.find_named_entity("Tom")
    dom = slr.memory.find_named_entity("Dom")
    assert tom is not None
    assert dom is not None
    assert slr.memory.canonical_entity(tom) == slr.memory.canonical_entity(dom)

    answer = slr.process("What is Tom?")
    assert "cat" in answer.lower()


def test_state_after_identity_updates_canonical_memory():
    slr = SLR()

    slr.process("Dom is my cat.")
    slr.process("Tom is Dom.")
    slr.process("Tom is hungry.")

    dom = slr.memory.find_named_entity("Dom")
    canonical = slr.memory.canonical_entity(dom)
    assert any(
        m.subject == canonical and m.predicate == "HUNGRY" and m.object == "TRUE"
        for m in slr.memory.memories
    )
