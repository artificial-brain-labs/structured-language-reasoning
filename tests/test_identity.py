from src.main import SLR


def test_explicit_entity_identity():
    slr = SLR()
    slr.process("Dom is my cat.")
    slr.process("Tom is Dom.")

    tom = slr.memory.find_named_entity("Tom")
    dom = slr.memory.find_named_entity("Dom")

    assert tom is not None
    assert dom is not None
    assert slr.memory.canonical_entity(tom) == slr.memory.canonical_entity(dom)


def test_identity_resolves_type():
    slr = SLR()
    slr.process("Dom is my cat.")
    slr.process("Tom is Dom.")

    answer = slr.process("What is Tom?")

    assert "cat" in answer.lower()


def test_identity_carries_observations_to_canonical_entity():
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
