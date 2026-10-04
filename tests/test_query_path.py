import pytest

from src.reasoning.query_path import QueryPath, QueryPathStep


def test_query_path_preserves_explicit_relation_sequence():
    path = QueryPath(
        start="animal_001",
        steps=(
            QueryPathStep("OWNS", "animal_002"),
            QueryPathStep("EATS", "thing_001"),
        ),
    )

    assert path.predicates == ("OWNS", "EATS")
    assert path.target == "thing_001"


def test_query_path_rejects_causal_edges():
    path = QueryPath(
        start="event_001",
        steps=(QueryPathStep("CAUSES", "event_002"),),
    )

    with pytest.raises(ValueError, match="CAUSAL_INFER"):
        path.validate()


def test_empty_path_targets_start():
    path = QueryPath(start="entity_001")
    assert path.target == "entity_001"
    assert path.predicates == ()
