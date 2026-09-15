from pathlib import Path

from src.main import SLR


def test_main_does_not_encode_query_type_semantics():
    source = Path("src/main.py").read_text(encoding="utf-8")
    forbidden = [
        'parsed.question_type == "TYPE"',
        'concept == "UNKNOWN"',
        'get(operation.predicate) or {}).get("type") == "IDENTITY"',
    ]
    for fragment in forbidden:
        assert fragment not in source


def test_query_behavior_is_loaded_from_declarative_policy():
    slr = SLR()
    assert "TYPE" in slr.query.policy
    assert slr.query.policy["TYPE"]["result_kind"] == "entity_type"


def test_query_responses_are_loaded_from_declarative_knowledge():
    slr = SLR()
    slr.process("Dom is my cat.")
    response = slr.process("What is Dom?")
    assert response == "Dom is a cat."
