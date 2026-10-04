from src.main import SLR
from src.reasoning.query_integration import SRSTQueryReasoner
from src.reasoning.query_path import QueryPath, QueryPathStep


def test_explicit_query_path_uses_relational_traverse():
    slr = SLR()
    cat = slr.memory.find_entity("ANIMAL")
    dog = slr.memory.find_entity("ANIMAL")
    mouse = slr.memory.find_entity("THING")

    slr.memory.add_memory(cat, "OWNS", dog)
    slr.memory.add_memory(dog, "EAT", mouse)

    path = QueryPath(
        start=cat,
        steps=(
            QueryPathStep("OWNS", dog),
            QueryPathStep("EAT", mouse),
        ),
    )

    result, state = SRSTQueryReasoner(
        slr.memory, slr.lexicon
    ).answer_path(path)

    assert result == mouse
    assert state.history
    assert all(
        state.proof.has_node(claim_id)
        for claim_id in (
            "query_anchor",
            "traverse_query_anchor_OWNS_" + dog,
        )
    )
    assert state.proof.has_node("query_path")


def test_explicit_path_does_not_turn_arbitrary_edges_into_inference():
    slr = SLR()
    cat = slr.memory.find_entity("ANIMAL")
    dog = slr.memory.find_entity("ANIMAL")
    mouse = slr.memory.find_entity("THING")

    slr.memory.add_memory(cat, "OWNS", dog)
    slr.memory.add_memory(dog, "EAT", mouse)

    path = QueryPath(
        start=cat,
        steps=(QueryPathStep("EAT", mouse),),
    )

    result, state = SRSTQueryReasoner(
        slr.memory, slr.lexicon
    ).answer_path(path)

    assert result is None
    assert state.history == []
    assert not state.goal.status.value == "satisfied"


def test_conflicted_edges_are_not_traversable():
    slr = SLR()
    cat = slr.memory.find_entity("ANIMAL")
    dog = slr.memory.find_entity("ANIMAL")

    slr.memory.add_memory(cat, "OWNS", dog)
    slr.memory.add_memory(cat, "NOT_OWNS", dog)

    path = QueryPath(
        start=cat,
        steps=(QueryPathStep("OWNS", dog),),
    )

    result, state = SRSTQueryReasoner(
        slr.memory, slr.lexicon
    ).answer_path(path)

    assert result is None
    assert state.history == []


def test_causal_path_is_rejected_before_reasoning():
    slr = SLR()
    path = QueryPath(
        start="event_001",
        steps=(QueryPathStep("CAUSES", "event_002"),),
    )

    import pytest

    with pytest.raises(ValueError):
        SRSTQueryReasoner(slr.memory, slr.lexicon).answer_path(path)
