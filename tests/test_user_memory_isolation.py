from src.main import SLR


def test_user_knowledge_is_not_written_to_system_memory():
    slr = SLR()

    slr.process("Tom is a cat.")

    assert slr.memory.find_named_entity("Tom") is None
    assert not any(memory.predicate == "IS_A" for memory in slr.memory.memories)

    tom = slr.user_memory.find_named_entity("Tom")
    cat = slr.user_memory.find_entity("CAT")
    assert tom is not None
    assert any(
        memory.subject == tom
        and memory.predicate == "IS_A"
        and memory.object == cat
        and memory.status == "ASSERTED"
        for memory in slr.user_memory.memories
    )


def test_derived_knowledge_is_not_promoted_to_user_memory():
    slr = SLR()
    slr.process("Tom is a cat.")

    before = len(slr.user_memory.memories)
    result = slr.process("Is Tom an animal?")
    after = len(slr.user_memory.memories)

    assert "animal" in result.lower()
    assert after == before
    assert not any(
        memory.predicate == "IS_A"
        and memory.object == slr.user_memory.find_entity("ANIMAL")
        and memory.status == "ASSERTED"
        for memory in slr.user_memory.memories
    )


def test_separate_slr_instances_have_separate_user_memory():
    first = SLR()
    second = SLR()

    first.process("Tom is a cat.")

    assert first.user_memory.find_named_entity("Tom") is not None
    assert second.user_memory.find_named_entity("Tom") is None
