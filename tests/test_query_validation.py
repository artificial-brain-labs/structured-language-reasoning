from src.reasoning.proof import ProofNode
from src.reasoning.query_validation import validate_query_result
from src.reasoning.state import (
    Claim,
    Goal,
    GoalStatus,
    ReasoningState,
    ValidationStatus,
)


def test_derived_query_result_requires_valid_dependency_chain():
    state = ReasoningState(
        goal=Goal(id="goal", target="test"),
    )
    state.add_claim(
        Claim(
            id="derived",
            subject="cat",
            predicate="SEES",
            object="mouse",
            status=ValidationStatus.DERIVED,
            dependencies=["missing"],
        )
    )
    state.proof.add_node(ProofNode("derived", "claim", "derived"))
    state.proof.add_node(ProofNode("goal", "goal", "goal"))
    state.goal.status = GoalStatus.SATISFIED

    assert not validate_query_result(state, "derived")


def test_derived_query_result_requires_proof_node():
    state = ReasoningState(
        goal=Goal(id="goal", target="test"),
    )
    state.add_claim(
        Claim(
            id="derived",
            subject="cat",
            predicate="SEES",
            object="mouse",
            status=ValidationStatus.DERIVED,
            dependencies=[],
        )
    )
    state.proof.add_node(ProofNode("goal", "goal", "goal"))
    state.goal.status = GoalStatus.SATISFIED

    assert not validate_query_result(state, "derived")


def test_derived_query_result_with_observed_dependency_is_valid():
    state = ReasoningState(
        goal=Goal(id="goal", target="test"),
    )
    state.add_claim(
        Claim(
            id="observed",
            subject="cat",
            predicate="SEES",
            object="mouse",
            status=ValidationStatus.OBSERVED,
        )
    )
    state.add_claim(
        Claim(
            id="derived",
            subject="mouse",
            predicate="OCCURS",
            object=None,
            status=ValidationStatus.DERIVED,
            dependencies=["observed"],
        )
    )
    state.proof.add_node(ProofNode("observed", "claim", "observed"))
    state.proof.add_node(ProofNode("derived", "claim", "derived"))
    state.proof.add_node(ProofNode("goal", "goal", "goal"))
    state.goal.status = GoalStatus.SATISFIED

    assert validate_query_result(state, "derived")
