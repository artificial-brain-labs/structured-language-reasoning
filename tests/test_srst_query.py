from src.main import SLR
from src.reasoning.query_integration import SRSTQueryReasoner


def test_direct_object_query_is_proven_without_operator():
    slr = SLR()
    slr.process("The cat eats the mouse.")

    results, state = SRSTQueryReasoner(slr.memory, slr.lexicon).answer(
        slr.parser.parse("What does the cat eat?")
    )

    assert results == [slr.memory.find_entity("THING")]
    assert state.goal.status.value == "satisfied"
    assert state.step == 0
    assert state.history == []
    assert state.proof.has_node("query_object")


def test_direct_subject_query_is_proven_without_operator():
    slr = SLR()
    slr.process("The cat eats the mouse.")

    results, state = SRSTQueryReasoner(slr.memory, slr.lexicon).answer(
        slr.parser.parse("Who eats the mouse?")
    )

    assert results == [slr.memory.find_entity("ANIMAL")]
    assert state.goal.status.value == "satisfied"
    assert state.step == 0
    assert state.history == []


def test_conflicted_memory_cannot_support_query():
    slr = SLR()
    slr.process("The cat eats the mouse.")
    slr.process("The cat does not eat the mouse.")

    results, state = SRSTQueryReasoner(slr.memory, slr.lexicon).answer(
        slr.parser.parse("What does the cat eat?")
    )

    assert results == []
    assert state.goal.status.value == "open"
    assert not state.proof.has_node("query_object")


def test_unknown_query_does_not_become_false():
    slr = SLR()

    results, state = SRSTQueryReasoner(slr.memory, slr.lexicon).answer(
        slr.parser.parse("What does the cat eat?")
    )

    assert results == []
    assert state.goal.status.value == "open"
    assert all(
        claim.status.value != "contradicted"
        for claim in state.claims.values()
    )
