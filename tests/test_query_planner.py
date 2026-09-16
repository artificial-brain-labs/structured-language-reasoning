from src.main import SLR
from src.query_planner import QueryPlanner


def test_query_planner_uses_policy_handler():
    planner = QueryPlanner({
        "TYPE": {
            "result_kind": "entity_type",
            "handler": "_entity_type",
            "unknown_result": "unknown_type",
        }
    })

    plan = planner.plan(type("Parsed", (), {"question_type": "TYPE"})())

    assert plan["result_kind"] == "entity_type"
    assert plan["handler"] == "_entity_type"


def test_identity_proof_starts_from_explicit_subject():
    slr = SLR()
    slr.process("Tom is a cat.")
    slr.process("Dom is Tom.")

    answer = slr.process("Is Tom an animal?")

    assert "Tom -> CAT -> FELINE -> MAMMAL -> ANIMAL" in answer
    assert "Dom -> Tom" not in answer


def test_identity_proof_traverses_when_subject_is_alias():
    slr = SLR()
    slr.process("Tom is a cat.")
    slr.process("Dom is Tom.")

    answer = slr.process("Is Dom an animal?")

    assert "Dom -> Tom -> CAT -> FELINE -> MAMMAL -> ANIMAL" in answer
