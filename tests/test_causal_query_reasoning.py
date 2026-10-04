from src.main import SLR
from src.reasoning.causal_path import CausalPath, CausalPathStep
from src.reasoning.query_integration import SRSTQueryReasoner


def test_explicit_causal_query_uses_causal_infer():
    slr = SLR()
    rain = slr.memory.find_entity("WEATHER")
    wet = slr.memory.find_entity("THING")
    slr.memory.add_memory(rain, "CAUSES", wet)

    path = CausalPath(
        cause=rain,
        steps=(CausalPathStep(wet),),
    )

    result, state = SRSTQueryReasoner(
        slr.memory, slr.lexicon
    ).answer_causal_path(path)

    assert result == wet
    assert state.history
    assert state.history[0].startswith("causal_infer_")
    assert state.proof.has_node("causal_query")
    assert state.proof.has_node(
        "cause_causal_query_anchor_" + wet
    )


def test_causal_inference_does_not_use_noncausal_edges():
    slr = SLR()
    rain = slr.memory.find_entity("WEATHER")
    wet = slr.memory.find_entity("THING")
    slr.memory.add_memory(rain, "PRECEDES", wet)

    path = CausalPath(
        cause=rain,
        steps=(CausalPathStep(wet),),
    )

    result, state = SRSTQueryReasoner(
        slr.memory, slr.lexicon
    ).answer_causal_path(path)

    assert result is None
    assert state.history == []


def test_conflicted_causal_edge_cannot_support_effect():
    slr = SLR()
    rain = slr.memory.find_entity("WEATHER")
    wet = slr.memory.find_entity("THING")
    slr.memory.add_memory(rain, "CAUSES", wet)
    slr.memory.add_memory(rain, "NOT_CAUSES", wet)

    path = CausalPath(
        cause=rain,
        steps=(CausalPathStep(wet),),
    )

    result, state = SRSTQueryReasoner(
        slr.memory, slr.lexicon
    ).answer_causal_path(path)

    assert result is None
    assert state.history == []
