from src.reasoning.controller import OperatorController
from src.reasoning.operators import (
    Backtrack,
    CausalInfer,
    DecompPlan,
    Monitor,
    RelationalTraverse,
    ReprReframe,
    default_operators,
)
from src.reasoning.state import (
    Claim,
    Evidence,
    Goal,
    GoalStatus,
    ReasoningState,
    ValidationStatus,
)


def state(target="answer"):
    return ReasoningState(goal=Goal(id="g1", target=target))


def test_decomp_plan_creates_subgoals():
    s = state("find A AND find B")
    op = DecompPlan()
    assert op.applicable(s)
    assert op.necessary(s)

    s, t = op.execute(s)

    assert [g.target for g in s.subgoals] == ["find A", "find B"]
    assert t.operator == "DECOMP_PLAN"


def test_relational_traverse_is_not_causal_inference():
    s = state()
    s.claims["c1"] = Claim(
        "c1", "cat", "SEES", "mouse",
        status=ValidationStatus.OBSERVED,
        confidence=1.0,
    )
    s.relations.append(("mouse", "LOCATED_IN", "house"))

    s, _ = RelationalTraverse().execute(s)

    derived = s.claims["traverse_c1_LOCATED_IN_house"]
    assert derived.predicate == "LOCATED_IN"


def test_causal_infer_requires_explicit_causal_edge():
    s = state()
    s.claims["c1"] = Claim(
        "c1", "rain", "OCCURS", None,
        status=ValidationStatus.OBSERVED,
        confidence=1.0,
    )
    s.relations.append(("rain", "CAUSES", "wet_ground"))

    assert CausalInfer().applicable(s)
    s, _ = CausalInfer().execute(s)

    assert s.claims["cause_c1_wet_ground"].predicate == "OCCURS"
    assert s.claims["cause_c1_wet_ground"].subject == "wet_ground"


def test_relational_traverse_does_not_consume_causal_edges():
    s = state()
    s.claims["c1"] = Claim(
        "weather", "CONTAINS", "rain",
        status=ValidationStatus.OBSERVED,
        confidence=1.0,
    )
    s.relations.append(("rain", "CAUSES", "wet_ground"))

    assert not RelationalTraverse().applicable(s)


def test_reframe_changes_representation_not_claims():
    s = state()
    original = Claim(
        "c1", "cat", "EATS", "mouse",
        status=ValidationStatus.OBSERVED,
    )
    s.add_claim(original)
    s.assumptions.append("representation_blocked:graph")

    s, _ = ReprReframe().execute(s)

    assert s.representation == "graph"
    assert s.claims["c1"] == original


def test_monitor_uses_explicit_evidence():
    s = state()
    s.add_claim(
        Claim(
            "c1", "cat", "EATS", "mouse",
            status=ValidationStatus.UNKNOWN,
        )
    )
    s.evidence["e1"] = Evidence(
        id="e1",
        source="user",
        content="The cat eats the mouse.",
        evidence_type="assertion",
        reliability=0.9,
        supports=["c1"],
    )

    s, _ = Monitor().execute(s)

    assert s.claims["c1"].status == ValidationStatus.SUPPORTED
    assert s.claims["c1"].confidence == 0.9


def test_backtrack_only_invalidates_dependents():
    s = state()
    s.add_claim(
        Claim(
            "bad", "A", "IS", "B",
            status=ValidationStatus.CONTRADICTED,
        )
    )
    s.add_claim(
        Claim(
            "derived", "B", "IS", "C",
            status=ValidationStatus.DERIVED,
            dependencies=["bad"],
        )
    )
    s.add_claim(
        Claim(
            "unrelated", "X", "IS", "Y",
            status=ValidationStatus.DERIVED,
        )
    )

    assert Backtrack().applicable(s)
    s, _ = Backtrack().execute(s)

    assert s.claims["derived"].status == ValidationStatus.UNKNOWN
    assert s.claims["unrelated"].status == ValidationStatus.DERIVED


def test_default_operator_set_contains_six_operators():
    assert [op.name for op in default_operators()] == [
        "DECOMP_PLAN",
        "RELATIONAL_TRAVERSE",
        "CAUSAL_INFER",
        "REPR_REFRAME",
        "MONITOR",
        "BACKTRACK",
    ]


def test_controller_executes_only_a_necessary_operator():
    s = state()
    s.assumptions.append("representation_blocked:graph")
    controller = OperatorController([ReprReframe()])

    s, result = controller.reason(s, max_steps=1)

    assert s.representation == "graph"
    assert s.step == 1
    assert result.reason == "goal not satisfied"
