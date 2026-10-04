from src.reasoning.controller import CognitiveOperator, OperatorController
from src.reasoning.proof import ProofEdge, ProofNode
from src.reasoning.state import (
    Claim,
    Conflict,
    Goal,
    GoalStatus,
    ReasoningState,
    ValidationStatus,
)
from src.reasoning.termination import check_termination
from src.reasoning.transition import Transition
from src.reasoning.validation import validate_state


def make_state():
    return ReasoningState(goal=Goal(id="g1", target="answer"))


def test_unknown_is_not_false():
    state = make_state()
    state.add_claim(
        Claim(
            id="c1",
            subject="cat",
            predicate="eats",
            object="mouse",
            status=ValidationStatus.UNKNOWN,
        )
    )
    assert not validate_state(state)
    assert state.claims["c1"].status == ValidationStatus.UNKNOWN


def test_validation_distinguishes_contradiction_and_unknown():
    state = make_state()
    unknown = Claim(
        id="unknown",
        subject="cat",
        predicate="eats",
        object="mouse",
        status=ValidationStatus.UNKNOWN,
    )
    contradicted = Claim(
        id="contradicted",
        subject="cat",
        predicate="eats",
        object="bird",
        status=ValidationStatus.CONTRADICTED,
    )
    state.add_claim(unknown)
    state.add_claim(contradicted)

    assert unknown.status != contradicted.status
    assert not validate_state(state)


def test_transition_advances_exactly_one_step():
    transition = Transition(
        id="t1",
        previous_step=2,
        resulting_step=3,
        operator="MONITOR",
        trigger="unresolved evidence",
    )
    assert transition.is_valid_step()


def test_transition_rejects_non_sequential_step():
    transition = Transition(
        id="t1",
        previous_step=2,
        resulting_step=5,
        operator="MONITOR",
        trigger="unresolved evidence",
    )
    assert not transition.is_valid_step()


def test_proof_graph_records_derivation():
    state = make_state()
    state.proof.add_node(ProofNode("c1", "claim", "c1"))
    state.proof.add_node(ProofNode("g1", "goal", "g1"))
    state.proof.add_edge(ProofEdge("c1", "g1", "supports"))

    assert state.proof.has_node("g1")
    assert state.proof.dependencies_for("g1") == ["c1"]


def test_termination_requires_all_criteria():
    state = make_state()
    state.goal.status = GoalStatus.SATISFIED

    result = check_termination(state)
    assert not result.terminated
    assert not result.proof_complete

    state.proof.add_node(ProofNode("g1", "goal", "g1"))
    result = check_termination(state)

    assert result.terminated
    assert result.goal_satisfied
    assert result.evidence_sufficient
    assert result.semantically_valid
    assert result.no_critical_conflict
    assert result.proof_complete


def test_termination_rejects_unresolved_conflict():
    state = make_state()
    state.goal.status = GoalStatus.SATISFIED
    state.proof.add_node(ProofNode("g1", "goal", "g1"))
    state.add_conflict(
        Conflict(
            id="x1",
            claim_a="c1",
            claim_b="c2",
            reason="opposite predicates",
        )
    )

    result = check_termination(state)
    assert not result.terminated
    assert not result.no_critical_conflict


class NeverNecessaryOperator(CognitiveOperator):
    name = "NEVER_NEEDED"

    def applicable(self, state):
        return True

    def necessary(self, state):
        return False

    def execute(self, state):
        raise AssertionError("A non-necessary operator must never execute")


def test_controller_requires_necessity():
    state = make_state()
    controller = OperatorController([NeverNecessaryOperator()])
    _, result = controller.reason(state, max_steps=1)

    assert not result.terminated
    assert result.reason == "goal not satisfied"
