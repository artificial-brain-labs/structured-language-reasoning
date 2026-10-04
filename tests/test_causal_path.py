import pytest

from src.reasoning.causal_path import CausalPath, CausalPathStep


def test_causal_path_is_distinct_from_relational_query_path():
    path = CausalPath(
        cause="rain",
        steps=(CausalPathStep("wet_ground"),),
    )

    assert path.cause == "rain"
    assert path.target == "wet_ground"
    assert path.effects == ("wet_ground",)


def test_empty_causal_path_is_invalid():
    with pytest.raises(ValueError):
        CausalPath(cause="rain").validate()
